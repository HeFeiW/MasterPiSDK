"""
用于数字检测的YOLOv5模型应用
"""

import numpy as np
import cv2
import sys
sys.path.append("/root/ACLLite/python")
sys.path.append('/root/thuei-1/sdk-python/')
import time
import yaml_handle
import torch
import torchvision
from acllite_resource import AclLiteResource
from acllite_model import AclLiteModel
from acllite_imageproc import AclLiteImageProc
from acllite_image import AclLiteImage
from PIL import Image

# 数字标签
#LABELS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
LABELS = ["kettle", "mop", "dishcloth"]
class YOLOv5Detector:
    """YOLOv5模型用于数字检测"""
    def __init__(self, model_path, model_width=640, model_height=640):
        self.model_path = model_path
        self.model_width = model_width
        self.model_height = model_height
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self._resource = None
        self._dvpp = None

    def init_resource(self):
        """初始化资源"""
        self._resource = AclLiteResource()
        self._resource.init()
        self._dvpp = AclLiteImageProc(self._resource)
        self._model = AclLiteModel(self.model_path)
        print(f"YOLOv5 model initialized on {self.device}")

    def preprocess(self, frame):
        """预处理图像以适配YOLOv5模型输入"""
        self.original_image = frame
        self.original_height, self.original_width = frame.shape[:2]
        
        # 调整大小到模型输入尺寸，保持宽高比
        img = frame.copy()
        
        # 计算缩放比例和填充
        ratio = min(self.model_width / self.original_width, self.model_height / self.original_height)
        new_width = int(self.original_width * ratio)
        new_height = int(self.original_height * ratio)
        
        # 缩放图像
        resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # 创建填充后的图像
        self.resized_image = np.full((self.model_height, self.model_width, 3), 
                              (114, 114, 114), dtype=np.uint8)  # 填充灰色
        
        # 将缩放后的图像放置在中心
        dw, dh = (self.model_width - new_width) // 2, (self.model_height - new_height) // 2
        self.resized_image[dh:dh+new_height, dw:dw+new_width] = resized_img
        
        # 记录缩放和偏移信息，用于后处理
        self.scale_ratio = ratio
        self.padding = (dw, dh)
        
        return self.resized_image

    def infer(self):
        """执行推理"""
        try:
            # ACL模型执行
            result = self._model.execute([self.resized_image])
            
            # 转换为PyTorch tensor并处理
            if isinstance(result, list) and len(result) > 0:
                # 确保结果是正确的形状
                predictions = torch.tensor(result[0], device=self.device)
                
                # 根据YOLO输出格式调整维度
                if len(predictions.shape) == 1:
                    # 重塑一维输出为正确的YOLO输出格式
                    num_boxes = predictions.shape[0] // 85  # 假设每个框85个值(4个坐标+1个conf+80个类别)
                    predictions = predictions.reshape(1, num_boxes, 85)
                
                return predictions
            else:
                print("推理结果为空或格式错误")
                return torch.zeros((1, 0, 85), device=self.device)  # 返回空预测
                
        except Exception as e:
            print(f"推理错误: {e}")
            return torch.zeros((1, 0, 85), device=self.device)  # 返回空预测

    @staticmethod
    def xywh2xyxy(x):
        """将[x, y, w, h]转换为[x1, y1, x2, y2]格式"""
        y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
        y[..., 0] = x[..., 0] - x[..., 2] / 2  # top left x
        y[..., 1] = x[..., 1] - x[..., 3] / 2  # top left y
        y[..., 2] = x[..., 0] + x[..., 2] / 2  # bottom right x
        y[..., 3] = x[..., 1] + x[..., 3] / 2  # bottom right y
        return y
    
    @staticmethod
    def box_iou(box1, box2, eps=1e-7):
        """计算两组框的交并比"""
        (a1, a2), (b1, b2) = box1.unsqueeze(1).chunk(2, 2), box2.unsqueeze(0).chunk(2, 2)
        inter = (torch.min(a2, b2) - torch.max(a1, b1)).clamp(0).prod(2)
        return inter / ((a2 - a1).prod(2) + (b2 - b1).prod(2) - inter + eps)

    def non_max_suppression(
        self,
        prediction,
        conf_thres=0.25,
        iou_thres=0.45,
        classes=None,
        agnostic=False,
        multi_label=False,
        labels=(),
        max_det=300,
        nm=0,  # number of masks
    ):
        """
        非极大值抑制，剔除重叠的检测框
        返回：每个图像的检测结果列表，每个结果为(n,6)张量 [xyxy, conf, cls]
        """
        # 输入检查
        assert 0 <= conf_thres <= 1, f"无效的置信度阈值 {conf_thres}, 有效值在0.0和1.0之间"
        assert 0 <= iou_thres <= 1, f"无效的IoU阈值 {iou_thres}, 有效值在0.0和1.0之间"
        
        # 如果prediction是元组/列表（YOLOv5验证模式的输出）
        if isinstance(prediction, (list, tuple)):
            prediction = prediction[0]  # 仅选择推理输出

        device = prediction.device
        mps = "mps" in device.type  # Apple MPS
        if mps:  # MPS尚未完全支持，转换为CPU处理NMS
            prediction = prediction.cpu()
            
        bs = prediction.shape[0]  # 批大小
        nc = prediction.shape[2] - nm - 5  # 类别数量
        xc = prediction[..., 4] > conf_thres  # 候选框

        # 设置参数
        max_wh = 7680  # 最大框宽高（像素）
        max_nms = 30000  # torchvision.ops.nms()的最大框数
        time_limit = 0.5 + 0.05 * bs  # 退出前的时间限制（秒）
        redundant = True  # 要求冗余检测
        multi_label &= nc > 1  # 每个框多标签（增加0.5ms/img）
        merge = False  # 使用merge-NMS

        t = time.time()
        mi = 5 + nc  # mask起始索引
        output = [torch.zeros((0, 6 + nm), device=prediction.device)] * bs
        
        for xi, x in enumerate(prediction):  # 图像索引，图像推理
            # 应用约束条件
            x = x[xc[xi]]  # 置信度筛选

            # 如果有先验标签，则添加
            if labels and len(labels[xi]):
                lb = labels[xi]
                v = torch.zeros((len(lb), nc + nm + 5), device=x.device)
                v[:, :4] = lb[:, 1:5]  # box
                v[:, 4] = 1.0  # conf
                v[range(len(lb)), lb[:, 0].long() + 5] = 1.0  # cls
                x = torch.cat((x, v), 0)

            # 如果没有框，处理下一张图
            if not x.shape[0]:
                continue

            # 计算置信度
            x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

            # Box/Mask
            box = self.xywh2xyxy(x[:, :4])  # (center_x, center_y, width, height) to (x1, y1, x2, y2)
            mask = x[:, mi:]  # 如果没有masks，则为0列

            # 检测矩阵 nx6 (xyxy, conf, cls)
            if multi_label:
                i, j = (x[:, 5:mi] > conf_thres).nonzero(as_tuple=False).T
                x = torch.cat((box[i], x[i, 5 + j, None], j[:, None].float(), mask[i]), 1)
            else:  # 仅最佳类别
                conf, j = x[:, 5:mi].max(1, keepdim=True)
                x = torch.cat((box, conf, j.float(), mask), 1)[conf.view(-1) > conf_thres]

            # 按类别过滤
            if classes is not None:
                x = x[(x[:, 5:6] == torch.tensor(classes, device=x.device)).any(1)]

            # 检查形状
            n = x.shape[0]  # 框数量
            if not n:  # 无框
                continue
                
            # 按置信度排序并移除多余框
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]

            # 批处理NMS
            c = x[:, 5:6] * (0 if agnostic else max_wh)  # 类别
            boxes, scores = x[:, :4] + c, x[:, 4]  # 框（按类别偏移），分数
            i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
            i = i[:max_det]  # 限制检测数量
            
            if merge and (1 < n < 3e3):  # Merge NMS (框使用加权平均合并)
                # 更新框：boxes(i,4) = weights(i,n) * boxes(n,4)
                iou = self.box_iou(boxes[i], boxes) > iou_thres  # iou矩阵
                weights = iou * scores[None]  # 框权重
                x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(1, keepdim=True)  # 合并框
                if redundant:
                    i = i[iou.sum(1) > 1]  # 要求冗余性

            output[xi] = x[i]
            if mps:
                output[xi] = output[xi].to(device)
                
            # 时间限制
            if (time.time() - t) > time_limit:
                break

        return output

    def postprocess(self, results, frame=None):
        """后处理检测结果，转换回原始图像坐标"""
        if frame is None:
            frame = self.original_image.copy()
        
        detections = []
        
        # 处理结果
        for i, det in enumerate(results):  # 每张图的检测结果
            if len(det):
                # 恢复原始坐标
                det_scaled = det.clone()
                
                # 取消填充的影响
                det_scaled[:, 0] = (det_scaled[:, 0] - self.padding[0]) / self.scale_ratio  # x1
                det_scaled[:, 1] = (det_scaled[:, 1] - self.padding[1]) / self.scale_ratio  # y1
                det_scaled[:, 2] = (det_scaled[:, 2] - self.padding[0]) / self.scale_ratio  # x2
                det_scaled[:, 3] = (det_scaled[:, 3] - self.padding[1]) / self.scale_ratio  # y2
                
                # 限制在原始图像范围内
                det_scaled[:, [0, 2]] = det_scaled[:, [0, 2]].clamp(0, self.original_width)
                det_scaled[:, [1, 3]] = det_scaled[:, [1, 3]].clamp(0, self.original_height)
                
                # 可视化结果
                for *xyxy, conf, cls in det_scaled:
                    try:
                        cls_int = int(cls.item())
                        if cls_int < len(LABELS):  # 确保类别索引有效
                            x1, y1, x2, y2 = [int(x.item()) for x in xyxy]
                            
                            # 过滤掉太小的框
                            if (x2 - x1) < 10 or (y2 - y1) < 10:
                                continue
                                
                            # 保存检测结果
                            detections.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': conf.item(),
                                'class': cls_int,
                                'label': LABELS[cls_int]
                            })
                    except Exception as e:
                        print(f"处理检测结果时出错: {e}")
        
        return frame, detections

    def detect(self, frame):
        """完整的检测流程"""
        # 预处理
        self.preprocess(frame)
        
        # 推理
        predictions = self.infer()
        
        # 应用NMS
        results = self.non_max_suppression(
            predictions, 
            conf_thres=0.25,  # 置信度阈值
            iou_thres=0.45,   # IoU阈值
            classes=None,     # 过滤特定类别
            max_det=10        # 每张图最大检测数
        )
        
        # 后处理，在图像上绘制结果
        frame, detections = self.postprocess(results, frame)
        
        return frame, detections

    def release_resource(self):
        """释放资源"""
        if self._resource:
            del self._resource
        if self._dvpp:
            del self._dvpp
        if self._model:
            del self._model
        print("Resources released")

def find_camera_index():
    """找到可用的相机索引"""
    max_index = 10  # 要检查的最大索引
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            cap.release()
            return index
    raise ValueError("未找到相机")

def preprocess_image(img):
    """图像预处理：转灰度图、形态学处理"""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # 形态学操作，去除小噪声
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    
    try:
        cv2.imshow('binary', binary)
    except Exception as e:
        print(f"显示图像错误: {e}")
        
    return binary

def main():
    """主函数"""
    # 加载模型
    model_path = '/root/thuei-1/EdgeAndRobotics/Samples/YOLOV5USBCamera/model/best.om'
    model_width = 640
    model_height = 640
    
    detector = YOLOv5Detector(model_path, model_width, model_height)
    detector.init_resource()
    
    # 打开摄像头
    try:
        cap = cv2.VideoCapture("/dev/video0")
        if not cap.isOpened():
            raise ValueError("无法打开摄像头")
    except Exception as e:
        print(f"摄像头错误: {e}")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("无法获取帧")
                time.sleep(0.1)
                continue
            
            # 使用YOLOv5直接处理整个帧
            processed_frame, detections = detector.detect(frame)
            
            # 显示检测结果
            if detections:
                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    label = f"{det['label']} {det['confidence']:.2f}"
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(processed_frame, label, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 显示处理后的图像
            cv2.imshow('YOLOv5 Number Detection', processed_frame)
            
            # 按ESC退出
            key = cv2.waitKey(1)
            if key == 27:
                break
    
    except Exception as e:
        print(f"运行错误: {e}")
    
    finally:
        # 清理资源
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        detector.release_resource()

if __name__ == '__main__':
    main()