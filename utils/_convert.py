import cv2
import numpy as np

def estimate_square_pose(image, K, dist_coeffs, square_size=0.1):
    """
    估计红色方块在世界坐标系中的位置
    
    参数:
        image: 输入图像
        K: 相机内参矩阵, 3x3 numpy数组
        dist_coeffs: 相机畸变系数
        square_size: 方块的实际大小(米)
        
    返回:
        position: 方块中心在世界坐标系中的位置
        R: 旋转矩阵
        t: 平移向量
    """
    # 1. 预处理图像，提取红色区域
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 定义红色范围（可能需要根据具体环境调整）
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # 2. 提取轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None, None
    
    # 找到最大轮廓（假设是方块）
    max_contour = max(contours, key=cv2.contourArea)
    
    # 多边形近似，获取角点
    epsilon = 0.02 * cv2.arcLength(max_contour, True)
    approx = cv2.approxPolyDP(max_contour, epsilon, True)
    
    # 确保找到了四个角点（方块）
    if len(approx) != 4:
        return None, None, None
    
    # 对角点进行排序，确保顺序一致
    image_points = np.array([point[0] for point in approx], dtype=np.float32)
    
    # 按照左上、右上、右下、左下的顺序排列角点
    center = np.mean(image_points, axis=0)
    ordered_points = []
    
    for i in range(4):
        point = image_points[i]
        if point[0] < center[0] and point[1] < center[1]:
            ordered_points.append(point)  # 左上
    
    for i in range(4):
        point = image_points[i]
        if point[0] > center[0] and point[1] < center[1]:
            ordered_points.append(point)  # 右上
    
    for i in range(4):
        point = image_points[i]
        if point[0] > center[0] and point[1] > center[1]:
            ordered_points.append(point)  # 右下
            
    for i in range(4):
        point = image_points[i]
        if point[0] < center[0] and point[1] > center[1]:
            ordered_points.append(point)  # 左下
    
    image_points = np.array(ordered_points, dtype=np.float32)
    
    # 3. 定义方块在世界坐标系中的坐标
    # 假设方块中心在世界坐标系原点，方块平行于xOy平面
    half_size = square_size / 2
    object_points = np.array([
        [-half_size, -half_size, 0],  # 左上
        [half_size, -half_size, 0],   # 右上
        [half_size, half_size, 0],    # 右下
        [-half_size, half_size, 0]    # 左下
    ], dtype=np.float32)
    
    # 4. 使用PnP算法求解相机与方块之间的位姿关系
    success, rotation_vector, translation_vector = cv2.solvePnP(
        object_points, image_points, K, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    
    if not success:
        return None, None, None
    
    # 5. 将旋转向量转换为旋转矩阵
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    
    # 6. 计算方块中心在世界坐标系中的位置
    # 这里我们已经假设方块中心在局部坐标系原点
    # 所以方块中心的世界坐标就是平移向量
    position = translation_vector.flatten()
    
    # 如果已知相机的外参矩阵(R_c, t_c)，可以进一步转换到世界坐标系
    # R_world = R_c @ rotation_matrix
    # t_world = R_c @ translation_vector + t_c
    
    return position, rotation_matrix, translation_vector

# 示例使用
if __name__ == "__main__":
    # 相机内参（示例）
    K = np.array([
        [1000, 0, 320],
        [0, 1000, 240],
        [0, 0, 1]
    ])
    
    # 畸变系数（示例）
    dist_coeffs = np.zeros(5)
    
    # 假设我们已知相机外参
    R_camera = np.eye(3)  # 示例：单位矩阵
    t_camera = np.array([0, 0, 0])  # 示例：原点
    
    # 读取图像
    image = cv2.imread('red_square.jpg')
    
    # 获取方块位置
    position, R, t = estimate_square_pose(image, K, dist_coeffs, square_size=0.1)
    
    if position is not None:
        print("方块在相机坐标系中的位置:", position)
        
        # 转换到世界坐标系（如果已知相机外参）
        position_world = R_camera.dot(position) + t_camera
        print("方块在世界坐标系中的位置:", position_world)
    else:
        print("未能检测到方块")