import numpy as np

# 定义多个典型的 TriangleMesh 对象
init_mesh_data = [
    {
        "node": np.array([[0, 0], [1, 0], [0, 1]], dtype=np.float64),
        "edge": np.array([[0, 1], [2, 0], [1, 2]], dtype=np.int32), 
        "cell": np.array([[0, 1, 2]], dtype=np.int32),
        "face2cell": np.array([[0, 0, 2, 2], [0, 0, 1, 1], [0, 0, 0, 0]], dtype=np.int32),
        "NN": 3,
        "NE": 3,
        "NF": 3,
        "NC": 1
    },
    {
        "node": np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64),
        "edge": np.array([[0, 1], [2, 0], [3, 0], [1, 2], [2, 3]], dtype=np.int32),
        "cell": np.array([[1, 2, 0], [3, 0, 2]], dtype=np.int32),
        "face2cell": np.array([[0, 0, 1, 1], [0, 1, 0, 0], [1, 1, 2, 2], [0, 0, 2, 2],[1, 1, 1, 1]], dtype=np.int32),
        "NN": 4,
        "NE": 5, 
        "NF": 5,
        "NC": 2
    }
]

from_box_data= [
            {
                "node": np.array([[0 , 0], [0, 0.5], [0, 1], [0.5, 0], 
                    [0.5, 0.5], [0.5, 1], [1, 0], [1, 0.5], [1, 1]], dtype=np.float64),
                "edge": np.array([[1, 0], [0, 3], [4, 0], [2, 1], [1, 4], [5, 1], 
                    [5, 2], [3, 4], [3, 6], [7, 3], [4, 5], [4, 7], [8, 4], [8, 5], 
                    [6, 7], [7, 8]], dtype=np.int32), 
                "cell": np.array([[3, 4, 0], [6, 7, 3], [4, 5, 1], [7, 8, 4], 
                    [1, 0, 4], [4, 3, 7], [2, 1, 5], [5, 4, 8]], dtype=np.int32),
                "face2cell": np.array([[4, 4, 2, 2], [0, 0, 1, 1], [0, 4, 0, 0], [6, 6, 2, 2],
                    [2, 4, 1, 1], [2, 6, 0, 0], [6, 6, 1, 1], [0, 5, 2, 2], [1, 1, 1, 1], 
                    [1, 5, 0, 0], [2, 7, 2, 2], [3, 5, 1, 1], [3, 7, 0, 0], [7, 7, 1, 1], 
                    [1, 1, 2, 2], [3, 3, 2, 2]], dtype=np.int32),
                "NN": 9,
                "NE": 16,
                "NF": 16,
                "NC": 8
            }
]

entity_measure_data = [
        {
            "node_measure": np.array([0.0], dtype=np.float64),
            "edge_measure": np.array([1.0, 1.0, np.sqrt(2)], dtype=np.float64),
            "cell_measure": np.array([0.5], dtype=np.float64)
            }
]

grad_lambda_data = [
        {
            "val_shape": (62, 3, 2)}
]

interpolation_point_data = [
        {
            "ips": np.array([[0.  , 0.  ],
                [1.  , 0.  ],
                [0.  , 1.  ],
                [0.25, 0.  ],
                [0.5 , 0.  ],
                [0.75, 0.  ],
                [0.  , 0.75],
                [0.  , 0.5 ],
                [0.  , 0.25],
                [0.75, 0.25],
                [0.5 , 0.5 ],
                [0.25, 0.75],
                [0.25, 0.25],
                [0.5 , 0.25],
                [0.25, 0.5 ]], dtype=np.float64),
            "cip": np.array([[ 0,  3,  8,  4, 12,  7,  5, 13, 14,  
                6,  1,  9, 10, 11,  2]], dtype=np.int32),
            "fip": np.array([[ 0,  3,  4,  5,  1],
                [ 2,  6,  7,  8,  0], [ 1,  9, 10, 11,  2]], dtype=np.int32)
            }
] 

uniform_refine_data = [
        {
            "node": np.array([[0.  , 0.  ], [1.  , 0.  ], [0.  , 1.  ],
                [0.5 , 0.  ], [0.  , 0.5 ], [0.5 , 0.5 ], [0.25, 0.  ],
                [0.  , 0.25], [0.75, 0.  ], [0.75, 0.25], [0.  , 0.75],
                [0.25, 0.75], [0.25, 0.25], [0.5 , 0.25], [0.25, 0.5 ]], dtype=np.float64),
            "cell": np.array([[ 0,  6,  7], [ 3,  8, 13], [ 4, 14, 10],
                [ 5, 14, 13], [ 6,  3, 12], [ 8,  1,  9], [14,  5, 11], [14,  4, 12],
                [ 7, 12,  4], [13,  9,  5], [10, 11,  2], [13, 12,  3],
                [12,  7,  6], [ 9, 13,  8], [11, 10, 14], [12, 13, 14]], dtype=np.int32),
            "face2cell": np.array([[ 0,  0,  2,  2], [ 0,  0,  1,  1], [ 5,  5,  2,  2],
                [ 5,  5,  0,  0], [10, 10,  1,  1], [10, 10,  0,  0], [ 4,  4,  2,  2], 
                [ 1,  1,  2,  2], [ 4, 11,  0,  0], [ 1, 11,  1,  1], [ 8,  8,  1,  1], 
                [ 2,  2,  1,  1], [ 7,  8,  0,  0], [ 2,  7,  2,  2], [ 9,  9,  0,  0],
                [ 6,  6,  0,  0], [ 3,  9,  1,  1], [ 3,  6,  2,  2], [ 0, 12,  0,  0],
                [ 4, 12,  1,  1], [ 8, 12,  2,  2], [ 5, 13,  1,  1], [ 1, 13,  0,  0],
                [ 9, 13,  2,  2], [10, 14,  2,  2], [ 2, 14,  0,  0], [ 6, 14,  1,  1],
                [11, 15,  2,  2], [ 7, 15,  1,  1], [ 3, 15,  0,  0]], dtype=np.int32),
            "cell2edge": np.array([[18,  1,  0], [22,  9,  7], [25, 11, 13],
                [29, 16, 17], [ 8, 19,  6], [ 3, 21,  2], [15, 26, 17], 
                [12, 28, 13], [12, 10, 20], [14, 16, 23], [ 5,  4, 24], [ 8,  9, 27],
                [18, 19, 20], [22, 21, 23], [25, 26, 24], [29, 28, 27]], dtype=np.int32)
            }
]

from_torus_surface_data = [
        {"R": 3, "r": 1, "Nu": 20, "Nv": 20, "node_shape": (20*20, 3), "cell_shape": (2*20*20, 3)},
        {"R": 5, "r": 2, "Nu": 30, "Nv": 30, "node_shape": (30*30, 3), "cell_shape": (2*30*30, 3)},
        {"R": 4, "r": 1.5, "Nu": 15, "Nv": 10, "node_shape": (15*10, 3), "cell_shape": (2*15*10, 3)},
        {"R": 6, "r": 3, "Nu": 25, "Nv": 10, "node_shape": (25*10, 3), "cell_shape": (2*25*10, 3)}
]

