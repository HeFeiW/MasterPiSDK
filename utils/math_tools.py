import numpy as np
def least_squares_fit(center_points):
    """
    对中心点进行最小二乘拟合，返回斜率和相关系数 r。
    
    :param center_points: 中心点的列表 [(x1, y1), (x2, y2), ...]
    :return: (slope, r_value)
    """
    if len(center_points) < 2:
        raise ValueError("At least two points are required for fitting.")
    
    # 提取 x 和 y 坐标
    x = np.array([point[0] for point in center_points])
    y = np.array([point[1] for point in center_points])
    
    # 计算斜率和截距
    A = np.vstack([x, np.ones(len(x))]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    
    # 计算相关系数 r
    correlation_matrix = np.corrcoef(x, y)
    r_value = correlation_matrix[0, 1]
    
    return slope, r_value
