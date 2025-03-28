"""
Copyright (R) @huawei.com, all rights reserved
-*- coding:utf-8 -*-
CREATED:  2023-05-25 09:12:13
MODIFIED: 2023-05-25 10:10:55
"""


# import videocapture as video
import numpy as np
import cv2
import sys
sys.path.append("/root/ACLLite/python")  # 添加到文件开头
import time 

from acllite_resource import AclLiteResource
from acllite_model import AclLiteModel
from acllite_imageproc import AclLiteImageProc
from acllite_image import AclLiteImage
from acllite_logger import log_error, log_info

labels = ["kettle", "mop", "dishcloth"]

class sampleYOLOV7(object):
    '''load the model, and do preprocess, infer, postprocess'''
    def __init__(self, model_path, model_width, model_height):
        self.model_path = model_path
        self.model_width = model_width
        self.model_height = model_height

    def init_resource(self):
        # initial acl resource, create image processor, create model
        self._resource = AclLiteResource()
        self._resource.init()
    
        self._dvpp = AclLiteImageProc(self._resource) 
        self._model = AclLiteModel(self.model_path)

    def preprocess(self, frame):
        """
        Preprocess the input frame before inference:
        1. Resize to model dimensions
        2. Convert from BGR to RGB (if needed)
        3. Normalize pixel values
        4. Transpose to match model input requirements
        """
        # Create AclLiteImage from frame
        src_image = AclLiteImage(frame, frame.shape[0], frame.shape[1], 
                                AclLiteImage.PIXEL_FORMAT_BGR_888)
        # Resize image to model input dimensions
        self.resized_image = self._dvpp.resize(src_image, self.model_width, self.model_height)
        return self.resized_image

    def infer(self):
        # infer frame
        self.result = self._model.execute([self.resized_image])
    
    
    def postprocess(self):
        """
        Process the model output:
        1. Extract detection results from model output
        2. Apply non-max suppression (if needed)
        3. Draw bounding boxes and labels on the original frame
        4. Return the processed frame
        """
        # Parse the model output
        output_data = self.result[0]
        
        # Output is typically [batch_size, num_boxes, 85] for YOLOv7
        # Where 85 is [x, y, w, h, conf, class_0, class_1, ..., class_79]
        
        # Reshape the output to the expected format
        # Depends on your specific model implementation
        if len(output_data.shape) == 3:
            # Standard YOLOv7 output
            detection_results = output_data[0]  # First batch
        else:
            # Some models may output differently
            detection_results = output_data
        
        boxes = []
        confidences = []
        class_ids = []
        
        # Parse detection results
        # Assuming output format: [x, y, w, h, conf, class_probs...]
        conf_threshold = 0.5
        
        for detection in detection_results:
            # Get box confidence
            confidence = detection[4]
            
            if confidence > conf_threshold:
                # Get class with highest probability
                class_scores = detection[5:]
                class_id = np.argmax(class_scores)
                class_confidence = class_scores[class_id]
                
                if class_confidence > 0.5:  # Class confidence threshold
                    # YOLO outputs center (x, y) and width, height
                    cx, cy, w, h = detection[0:4]
                    
                    # Convert to top-left corner coordinates
                    x = cx - w/2
                    y = cy - h/2
                    
                    # Add to our lists
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply non-max suppression to remove overlapping boxes
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, 0.4)
        
        # For drawing purposes, convert image back to numpy array
        result_frame = self.resized_image.copy_to_numpy()
        
        # Get original height and width for scaling
        original_h, original_w = result_frame.shape[:2]
        
        # Draw boxes
        for i in indices:
            if isinstance(i, list) or isinstance(i, np.ndarray):  # Check for older OpenCV versions
                i = i[0]
            
            box = boxes[i]
            x, y, w, h = box
            
            # Scale to pixel coordinates
            x = int(x * original_w)
            y = int(y * original_h)
            w = int(w * original_w)
            h = int(h * original_h)
            
            # Draw bounding box
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Get label
            label = labels[class_ids[i]] if class_ids[i] < len(labels) else str(class_ids[i])
            confidence = confidences[i]
            
            # Draw label
            label_text = f"{label}: {confidence:.2f}"
            cv2.putText(result_frame, label_text, (x, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display the resulting frame
        cv2.imshow('out', result_frame)
        
        return result_frame

    def release_resource(self):
        # release resource includes acl resource, data set and unload model
        del self._resource
        del self._dvpp
        del self._model
        del self.resized_image

def find_camera_index():
    max_index_to_check = 10  # Maximum index to check for camera
    for index in range(max_index_to_check):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            cap.release()
            return index
    # If no camera is found
    raise ValueError("No camera found.")


if __name__ == '__main__':
    model_path = '/root/thuei-1/EdgeAndRobotics/Samples/YOLOV5USBCamera/model/numbers.om'
    model_width = 640
    model_height = 640
    model = sampleYOLOV7(model_path, model_width, model_height)
    model.init_resource()

    # camera_index = find_camera_index()
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('out', cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret:  
            print("Can't receive frame (stream end?). Exiting ...")  
            break  
        # print(f"图像形状: {frame.shape}") 
        # frame = cv2.resize(frame, (640, 640)) 
        # print(f"图像形状: {frame.shape}") 
        print(model.model_height,model.model_width, frame.shape, model.model_path)
        model.preprocess(frame)
        model.infer()
        model.postprocess()
        # cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  
            break  
    cap.release()  
    cv2.destroyAllWindows()
    
    model.release_resource()
