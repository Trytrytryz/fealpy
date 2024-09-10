from abc import ABC, abstractmethod
import numpy as np
from numpy import sin, cos, tan, pi, arctan, arctan2, radians, sqrt

from scipy.optimize import fsolve
from fealpy.experimental.mesh.quadrangle_mesh import QuadrangleMesh


class Gear(ABC):
    def __init__(self, m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf, material=None):
        """

        @param m_n: 法向模数
        @param z: 齿数
        @param alpha_n: 法向压力角
        @param beta: 螺旋角
        @param x_n: 法向变位系数
        @param hac: 齿顶高系数
        @param cc: 顶隙系数
        @param rcc: 刀尖圆弧半径系数系数
        @param jn: 法向侧隙
        @param n1: 渐开线分段数
        @param n2: 过渡曲线分段数
        @param n3: 齿轮内部分段书
        @param na: 齿顶分段数
        @param nf: 齿根圆部分分段数（一侧，非最大圆角时）
        @param material: 齿轮材料
        """
        if not isinstance(z, int) or (isinstance(z, float) and not z.is_integer()):
            raise TypeError(f'The provided value {z} is not an integer or cannot be safely converted to an integer.')
        self.m_n = m_n
        self.z = z
        self.alpha_n = alpha_n if alpha_n < 2 * pi else radians(alpha_n)
        self.beta = beta if beta < 2 * pi else radians(beta)
        self.x_n = x_n
        self.hac = hac
        self.cc = cc
        self.rcc = rcc
        self.jn = jn
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.na = na
        self.nf = nf
        self.mesh = None
        self._material = material

        # 端面变位系数
        self.x_t = self.x_n / cos(self.beta)
        # 端面压力角
        self.alpha_t = arctan(tan(self.alpha_n) / cos(self.beta))
        # 端面模数
        self.m_t = self.m_n / cos(self.beta)
        # 分度圆直径与半径
        self.d = self.m_t * self.z
        self.r = self.d / 2
        # 基圆（base circle）直径与半径
        self.d_b = self.d * cos(self.alpha_t)
        self.r_b = self.d_b / 2

    @abstractmethod
    def get_involute_points(self):
        pass

    @abstractmethod
    def get_tip_intersection_points(self):
        pass

    @abstractmethod
    def get_transition_points(self):
        pass

    @abstractmethod
    def get_profile_points(self):
        pass

    @abstractmethod
    def generate_mesh(self):
        pass

    def show_mesh(self, save_path=None):
        if self.mesh is None:
            raise AssertionError('The mesh is not yet created.')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(38, 20))
        self.mesh.add_plot(ax, linewidth=0.1)
        if save_path is not None:
            plt.savefig(save_path, dpi=600, bbox_inches='tight')
        plt.show()

    @property
    def material(self):
        return self._material

    @material.setter
    def value(self, new_material):
        self._material = new_material
        pass


class ExternalGear(Gear):
    def __init__(self, m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf, chamfer_dia, inner_diam):
        """

        @param m_n: 法向模数
        @param z: 齿数
        @param alpha_n: 法向压力角
        @param beta: 螺旋角
        @param x_n: 法向变位系数
        @param hac: 齿顶高系数
        @param cc: 顶隙系数
        @param rcc: 刀尖圆弧半径系数
        @param jn: 法向侧隙
        @param n1: 渐开线分段数
        @param n2: 过渡曲线分段数
        @param n3: 齿轮内部分段数
        @param na: 齿顶分段数
        @param nf: 齿根圆部分分段数（一侧，非最大圆角时）
        @param chamfer_dia: 倒角高度（直径方向）
        @param inner_diam: 轮缘内径
        """
        super().__init__(m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf)
        self.inner_diam = inner_diam
        self.chamfer_dia = chamfer_dia
        # 齿顶圆直径与半径
        ha = self.m_n * (self.hac + self.x_t)  # 齿顶高
        self.d_a = self.d + 2 * ha
        self.r_a = self.d_a / 2
        # 齿根圆直径与半径
        hf = self.m_n * (self.hac + self.cc - self.x_t)
        self.d_f = self.d - 2 * hf
        self.r_f = self.d_f / 2
        # 有效齿顶圆
        self.effective_da = self.d_a - self.chamfer_dia
        self.effective_ra = self.effective_da / 2
        # 刀具齿顶高与刀尖圆弧半径
        self.ha_cutter = (self.hac + self.cc) * self.m_n
        self.rc = self.m_n * self.rcc

    def get_involute_points(self, t):
        m_n = self.m_n
        alpha_t = self.alpha_t
        beta = self.beta
        r = self.r
        x_t = self.x_t

        k = -(np.pi * m_n / 4 + m_n * x_t * np.tan(alpha_t))
        phi = (t * np.cos(np.pi / 2 - alpha_t) ** 2 + k * np.cos(np.pi / 2 - alpha_t) + t * np.cos(beta) ** 2 * np.sin(
            np.pi / 2 - alpha_t) ** 2) / (r * np.cos(beta) * np.cos(np.pi / 2 - alpha_t))

        xt = (r * np.sin(phi) - phi * r * np.cos(phi) +
              t * np.sin(phi) * np.sin(np.pi / 2 - alpha_t) +
              (np.cos(phi) * (k + t * np.cos(np.pi / 2 - alpha_t))) / np.cos(beta)).reshape(-1, 1)

        yt = (r * np.cos(phi) + phi * r * np.sin(phi) +
              t * np.cos(phi) * np.sin(np.pi / 2 - alpha_t) -
              (np.sin(phi) * (k + t * np.cos(np.pi / 2 - alpha_t))) / np.cos(beta)).reshape(-1, 1)

        points = np.concatenate([xt, yt], axis=-1)
        return points

    def get_tip_intersection_points(self, t):

        points = self.get_involute_points(t)
        return np.sqrt(points[..., 0] ** 2 + points[..., 1] ** 2)

    def get_transition_points(self, t):
        r = self.r
        rc = self.rc  # 刀尖圆弧半径
        ha_cutter = self.ha_cutter  # 刀具齿顶高
        alpha_t = self.alpha_t
        beta = self.beta

        # 刀尖圆弧 y 坐标
        x0 = -np.pi * self.m_n / 2 + (np.pi * self.m_n / 4 - ha_cutter * np.tan(alpha_t) - rc * np.tan(
            0.25 * np.pi - 0.5 * alpha_t))
        # 刀尖圆弧 y 坐标
        y0 = -(ha_cutter - rc) + self.m_n * self.x_t

        phi = (x0 * np.sin(t) + rc * np.cos(t) * np.sin(t) - y0 * np.cos(beta) ** 2 * np.cos(
            t) - rc * np.cos(
            beta) ** 2 * np.cos(t) * np.sin(t)) / (r * np.cos(beta) * np.sin(t))

        xt = (r * np.sin(phi) + np.sin(phi) * (y0 + rc * np.sin(t)) - phi * r * np.cos(phi) +
              (np.cos(phi) * (x0 + rc * np.cos(t))) / np.cos(beta)).reshape(-1, 1)

        yt = (r * np.cos(phi) + np.cos(phi) * (y0 + rc * np.sin(t)) + phi * r * np.sin(phi) -
              (np.sin(phi) * (x0 + rc * np.cos(t))) / np.cos(beta)).reshape(-1, 1)

        points = np.concatenate([xt, yt], axis=-1)
        return points

    def get_profile_points(self):
        n1 = self.n1
        n2 = self.n2
        mn = self.m_n
        alpha_t = self.alpha_t
        beta = self.beta
        z = self.z
        x = self.x_t
        effective_da = self.effective_da
        ha_cutter = self.ha_cutter  # 刀具齿顶高
        rc = self.rc  # 刀尖圆弧半径

        points = np.zeros(((n1 + n2 + 1) * 2, 3))

        t1 = (mn * x - (ha_cutter - rc + rc * sin(alpha_t))) / cos(alpha_t)

        def involutecross(t2):
            return self.get_tip_intersection_points(t2) - (0.5 * effective_da)

        t2 = fsolve(involutecross, mn)[0]  # 求解渐开线与齿顶圆的交点

        t3 = 2 * np.pi - alpha_t
        t4 = 1.5 * np.pi
        width2 = t3 - t4
        t = np.linspace(t4, t3, n2+1)
        points[0:n2+1, 0:-1] = self.get_transition_points(t)

        width1 = t2 - t1
        t = np.linspace(t1+width1 / n1, t2, n1)
        points[n2+1:n2+n1+1, 0:-1] = self.get_involute_points(t)

        # 构建对称点
        points[n2+n1+1:, 0] = -points[0:n2+n1+1, 0]
        points[n2+n1+1:, 1] = points[0:n2+n1+1, 1]

        return points

    def generate_mesh(self):
        n1 = self.n1
        n2 = self.n2
        n3 = self.n3
        nf = self.nf
        na = self.na
        rf = self.r_f
        ra = self.effective_ra
        # 获取齿廓与过渡曲线点列
        points = self.get_profile_points()
        # 齿顶弧线，逆时针，角度参数 t_aa > t_a
        t_a = arctan2(points[-1, 1], points[-1, 0])
        t_aa = pi - t_a

        # 齿根部分
        t_ff = arctan2(points[0, 1], points[0, 0])
        t_f = pi - t_ff
        r_inner = self.inner_diam / 2
        theta = np.linspace(t_f, t_ff, 100)
        x_f = r_inner * cos(theta)
        y_f = r_inner * sin(theta)

        # 构造关键点
        kp_1 = points[n1 + n2 + 1]
        kp_4 = points[0]

        kp_2 = points[2 * n1 + n2 + 1]
        kp_5 = points[n1]

        kp_3 = points[-1]
        kp_6 = points[n1 + n2]

        kp_0 = np.array([x_f[0], y_f[0], 0])
        kp_11 = np.array([x_f[-1], y_f[-1], 0])

        kp_10 = np.array([0, r_inner, 0])
        kp_9 = np.array([0, ra, 0])

        # 单侧弧长与点数，计算中轴上点参数
        distance = np.sqrt(np.sum(np.diff(points[:n1 + n2 + 1], axis=0) ** 2, axis=1))
        length2 = np.sum(distance[:n1])
        length3 = np.sum(distance[n1:n1 + n2])
        length1 = np.sqrt(np.sum((kp_4 - kp_11) ** 2))

        n_total = n1 * 1.236 + n2 * 0.618 + n3
        length2_n = length2 * (n1 * 1.236 / n_total)
        length3_n = length3 * (n2 * 0.618 / n_total)
        length1_n = length1 * (n3 / n_total)
        length_total_n = length1_n + length2_n + length3_n

        t_2 = length2_n / length_total_n
        t_1 = length1_n / length_total_n

        kp_7 = np.array([0, r_inner + (ra - r_inner) * t_1, 0])
        kp_8 = np.array([0, r_inner + (ra - r_inner) * (t_1 + t_2), 0])

        # 旋转角
        rot_phi = np.linspace(0, 2 * np.pi, z, endpoint=False)

        # 齿根圆弧上点计算
        rot_kp_1 = np.zeros(2)
        rot_kp_1[0] = np.cos(rot_phi[1]) * kp_1[0] - np.sin(rot_phi[1]) * kp_1[1]
        rot_kp_1[1] = np.sin(rot_phi[1]) * kp_1[0] + np.cos(rot_phi[1]) * kp_1[1]
        angle0 = np.arctan2(kp_1[1], kp_1[0])
        angle1 = np.arctan2(rot_kp_1[1], rot_kp_1[0])
        angle2 = np.arctan2(kp_4[1], kp_4[0])
        delta_angle = abs(angle1 - angle2)

        # TODO: 改用齿根圆角是否超过最大圆角进行判断与分类
        # 两侧过渡曲线之间相连，齿槽底面为一条直线，宽度为 0
        if delta_angle < 1e-12:
            key_points = np.array([kp_0, kp_1, kp_2, kp_3, kp_4, kp_5, kp_6, kp_7, kp_8, kp_9, kp_10, kp_11])

            edge = np.array([[0, 1],
                             [1, 2],
                             [2, 3],
                             [10, 7],
                             [7, 8],
                             [8, 9],
                             [11, 4],
                             [4, 5],
                             [5, 6],
                             [10, 0],
                             [7, 1],
                             [8, 2],
                             [9, 3],
                             [11, 10],
                             [4, 7],
                             [5, 8],
                             [6, 9]])

            # 构建子区域半边数据结构
            half_edge = np.zeros((len(edge) * 2, 5), dtype=np.int64)
            half_edge[::2, 0] = edge[:, 1]
            half_edge[1::2, 0] = edge[:, 0]
            half_edge[::2, 4] = 2 * np.arange(len(edge)) + 1
            half_edge[1::2, 4] = 2 * np.arange(len(edge))
            half_edge[np.array([0, 1, 2]) * 2, 1] = np.array([0, 1, 2])
            half_edge[np.array([0, 1, 2]) * 2 + 1, 1] = -1
            half_edge[np.array([3, 4, 5]) * 2, 1] = np.array([3, 4, 5])
            half_edge[np.array([3, 4, 5]) * 2 + 1, 1] = np.array([0, 1, 2])
            half_edge[np.array([6, 7, 8]) * 2, 1] = -1
            half_edge[np.array([6, 7, 8]) * 2 + 1, 1] = np.array([3, 4, 5])
            half_edge[np.array([10, 11, 14, 15]) * 2, 1] = np.array([1, 2, 4, 5])
            half_edge[np.array([10, 11, 14, 15]) * 2 + 1, 1] = np.array([0, 1, 3, 4])
            half_edge[np.array([9, 13]) * 2, 1] = np.array([0, 3])
            half_edge[np.array([9, 13]) * 2 + 1, 1] = -1
            half_edge[np.array([12, 16]) * 2, 1] = -1
            half_edge[np.array([12, 16]) * 2 + 1, 1] = np.array([2, 5])

            half_edge[::2, 2] = np.array([21, 23, 25, 29, 31, 33, 14, 16, 32, 0, 2, 4, 5, 6, 8, 10, 24])
            half_edge[1::2, 2] = np.array([19, 1, 3, 18, 20, 22, 26, 28, 30, 27, 7, 9, 11, 12, 13, 15, 17])

            half_edge[::2, 3] = np.array([18, 20, 22, 26, 28, 30, 27, 12, 14, 7, 9, 11, 32, 13, 15, 17, 16])
            half_edge[1::2, 3] = np.array([3, 5, 24, 21, 23, 25, 29, 31, 33, 1, 0, 2, 4, 19, 6, 8, 10])

            theta_f = np.linspace(np.pi / 2, t_f, na + 1)
            theta_ff = np.linspace(t_ff, np.pi / 2, na + 1)
            theta_a = np.linspace(np.pi / 2, t_a, na + 1)
            theta_aa = np.linspace(t_aa, np.pi / 2, na + 1)
            line = [
                np.linspace(kp_0[..., :-1], kp_1[..., :-1], n3 + 1),
                points[n1 + n2 + 1:2 * n1 + n2 + 2, :-1],
                points[2 * n1 + n2 + 1:2 * n1 + 2 * n2 + 2, :-1],
                np.linspace(kp_10[..., :-1], kp_7[..., :-1], n3 + 1),
                np.linspace(kp_7[..., :-1], kp_8[..., :-1], n1 + 1),
                np.linspace(kp_8[..., :-1], kp_9[..., :-1], n2 + 1),
                np.linspace(kp_11[..., :-1], kp_4[..., :-1], n3 + 1),
                points[:n1 + 1, :-1],
                points[n1:n1 + n2 + 1, :-1],
                np.concatenate([r_inner * np.cos(theta_f)[:, None], r_inner * np.sin(theta_f)[:, None]], axis=1),
                np.linspace(kp_7[..., :-1], kp_1[..., :-1], na + 1),
                np.linspace(kp_8[..., :-1], kp_2[..., :-1], na + 1),
                np.concatenate([ra * np.cos(theta_a)[:, None], ra * np.sin(theta_a)[:, None]], axis=1),
                np.concatenate([r_inner * np.cos(theta_ff)[:, None], r_inner * np.sin(theta_ff)[:, None]], axis=1),
                np.linspace(kp_4[..., :-1], kp_7[..., :-1], na + 1),
                np.linspace(kp_5[..., :-1], kp_8[..., :-1], na + 1),
                np.concatenate([ra * np.cos(theta_aa)[:, None], ra * np.sin(theta_aa)[:, None]], axis=1)
            ]

            quad_mesh = QuadrangleMesh.sub_domain_mesh_generator(half_edge, key_points[:, :-1], line)
            tooth_node = quad_mesh.node
            tooth_cell = quad_mesh.cell
            origin_cell = quad_mesh.cell

            single_node_num = len(tooth_node) - (n3 + 1)
            temp_node = np.concatenate([tooth_node[2:len(key_points)], tooth_node[(len(key_points) + (n3 - 1)):]],
                                       axis=0)
            temp_node_last = np.concatenate([tooth_node[2:4],
                                             tooth_node[5:11],
                                             tooth_node[(len(key_points)+(n3-1)):(len(key_points)+2*(n1+n2+n3-3))],
                                             tooth_node[(len(key_points)+2*(n1+n2+n3-3)+n3-1):]], axis=0)
            # 左侧齿
            trans_matrix = np.arange(len(tooth_node))
            origin_trans_matrix = np.arange(len(tooth_node))
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[11]
            trans_matrix[1] = trans_matrix[4]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points) + n3 - 1] = trans_matrix[len(key_points) + 2 * (
                    n3 + n1 + n2 - 3):len(key_points) + 2 * (
                    n3 + n1 + n2 - 3) + n3 - 1]
            # 其他节点
            trans_matrix[2:len(key_points)] += single_node_num + n3 - 1
            trans_matrix[len(key_points) + n3 - 1:] += single_node_num

            rot_matrix = np.array([[np.cos(rot_phi[1]), -np.sin(rot_phi[1])], [np.sin(rot_phi[1]), np.cos(rot_phi[1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
            new_cell = trans_matrix[tooth_cell]

            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            # 中间齿
            for i in range(2, z - 1):
                rot_matrix = np.array(
                    [[np.cos(rot_phi[i]), -np.sin(rot_phi[i])], [np.sin(rot_phi[i]), np.cos(rot_phi[i])]])
                new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
                # 处理重复顶点
                trans_matrix[0] = trans_matrix[11]
                trans_matrix[1] = trans_matrix[4]
                # 处理重复边上节点
                trans_matrix[len(key_points):len(key_points) + n3 - 1] = trans_matrix[len(key_points) + 2 * (
                        n3 + n1 + n2 - 3):len(key_points) + 2 * (
                        n3 + n1 + n2 - 3) + n3 - 1]
                # 其他节点
                trans_matrix[2:len(key_points)] += single_node_num
                trans_matrix[len(key_points) + n3 - 1:] += single_node_num
                # 新单元映射与拼接
                new_cell = trans_matrix[origin_cell]
                tooth_node = np.concatenate([tooth_node, new_node], axis=0)
                tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            # 右侧齿
            rot_matrix = np.array(
                [[np.cos(rot_phi[-1]), -np.sin(rot_phi[-1])], [np.sin(rot_phi[-1]), np.cos(rot_phi[-1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node_last.T).T
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[11]
            trans_matrix[1] = trans_matrix[4]
            trans_matrix[11] = origin_trans_matrix[0]
            trans_matrix[4] = origin_trans_matrix[1]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points)+n3-1] \
                = trans_matrix[len(key_points)+2*(n3+n1+n2-3):len(key_points)+2*(n3+n1+n2-3)+n3-1]
            trans_matrix[len(key_points)+2*(n3+n1+n2-3):len(key_points)+2*(n3+n1+n2-3)+n3-1] \
                = origin_trans_matrix[len(key_points):len(key_points) + n3 - 1]
            # 其他节点
            trans_matrix[2:4] += single_node_num
            trans_matrix[5:11] += single_node_num - 1
            trans_matrix[(len(key_points) + (n3 - 1)):(len(key_points) + 2 * (n1 + n2 + n3 - 3))] += single_node_num - 2
            trans_matrix[(len(key_points) + 2 * (n1 + n2 + n3 - 3) + n3 - 1):] += single_node_num - 2 - (n3 - 1)
            # 新单元映射与拼接
            new_cell = trans_matrix[origin_cell]
            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            t_mesh = QuadrangleMesh(tooth_node, tooth_cell)
        else:
            # 计算边内部点数
            edge_node_num = (na - 1) * 8 + (n2 - 1) * 3 + (n1 - 1) * 3 + (n3 - 1) * 5 + (
                    nf - 1) * 4
            # 构造剩余关键点
            kp_12_angle = angle0 - delta_angle / 2
            kp_14_angle = angle2 + delta_angle / 2
            kp_12 = np.array([r_inner * np.cos(kp_12_angle), r_inner * np.sin(kp_12_angle), 0])
            kp_13 = np.array([rf * np.cos(kp_12_angle), rf * np.sin(kp_12_angle), 0])
            kp_14 = np.array([r_inner * np.cos(kp_14_angle), r_inner * np.sin(kp_14_angle), 0])
            kp_15 = np.array([rf * np.cos(kp_14_angle), rf * np.sin(kp_14_angle), 0])
            key_points = np.array(
                [kp_0, kp_1, kp_2, kp_3, kp_4, kp_5, kp_6, kp_7, kp_8, kp_9, kp_10, kp_11, kp_12, kp_13, kp_14, kp_15])
            # 构造半边数据结构所用分区边
            edge = np.array([[0, 1],
                             [1, 2],
                             [2, 3],
                             [10, 7],
                             [7, 8],
                             [8, 9],
                             [11, 4],
                             [4, 5],
                             [5, 6],
                             [10, 0],
                             [7, 1],
                             [8, 2],
                             [9, 3],
                             [11, 10],
                             [4, 7],
                             [5, 8],
                             [6, 9],
                             [12, 13],
                             [14, 15],
                             [0, 12],
                             [1, 13],
                             [14, 11],
                             [15, 4]])
            # 构建子区域半边数据结构
            half_edge = np.zeros((len(edge) * 2, 5), dtype=np.int64)
            half_edge[::2, 0] = edge[:, 1]
            half_edge[1::2, 0] = edge[:, 0]

            half_edge[::2, 4] = 2 * np.arange(len(edge)) + 1
            half_edge[1::2, 4] = 2 * np.arange(len(edge))

            half_edge[np.array([0, 1, 2]) * 2, 1] = np.array([0, 1, 2])
            half_edge[np.array([1, 2]) * 2 + 1, 1] = -1
            half_edge[0 * 2 + 1, 1] = 6
            half_edge[np.array([3, 4, 5]) * 2, 1] = np.array([3, 4, 5])
            half_edge[np.array([3, 4, 5]) * 2 + 1, 1] = np.array([0, 1, 2])
            half_edge[np.array([7, 8]) * 2, 1] = -1
            half_edge[6 * 2, 1] = 7
            half_edge[np.array([6, 7, 8]) * 2 + 1, 1] = np.array([3, 4, 5])
            half_edge[np.array([10, 11, 14, 15]) * 2, 1] = np.array([1, 2, 4, 5])
            half_edge[np.array([10, 11, 14, 15]) * 2 + 1, 1] = np.array([0, 1, 3, 4])
            half_edge[np.array([9, 13]) * 2, 1] = np.array([0, 3])
            half_edge[np.array([9, 13]) * 2 + 1, 1] = -1
            half_edge[np.array([12, 16]) * 2, 1] = -1
            half_edge[np.array([12, 16]) * 2 + 1, 1] = np.array([2, 5])
            half_edge[17 * 2, 1] = 6
            half_edge[17 * 2 + 1, 1] = -1
            half_edge[18 * 2, 1] = -1
            half_edge[18 * 2 + 1, 1] = 7
            half_edge[np.array([19, 21]) * 2, 1] = np.array([6, 7])
            half_edge[np.array([19, 21]) * 2 + 1, 1] = -1
            half_edge[np.array([20, 22]) * 2, 1] = -1
            half_edge[np.array([20, 22]) * 2 + 1, 1] = np.array([6, 7])

            half_edge[::2, 2] = np.array(
                [21, 23, 25, 29, 31, 33, 45, 16, 32, 0, 2, 4, 5, 6, 8, 10, 24, 41, 44, 34, 35, 12, 14])
            half_edge[1::2, 2] = np.array(
                [38, 40, 3, 18, 20, 22, 26, 28, 30, 27, 7, 9, 11, 43, 13, 15, 17, 39, 42, 19, 1, 36, 37])

            half_edge[::2, 3] = np.array(
                [18, 20, 22, 26, 28, 30, 42, 44, 14, 7, 9, 11, 32, 13, 15, 17, 16, 38, 43, 1, 3, 37, 36])
            half_edge[1::2, 3] = np.array(
                [41, 5, 24, 21, 23, 25, 29, 31, 33, 39, 0, 2, 4, 19, 6, 8, 10, 40, 45, 35, 34, 27, 12])
            # 构建半边数据结构所用边（由点列构成的边）
            theta_f = np.linspace(np.pi / 2, t_f, na + 1)
            theta_ff = np.linspace(t_ff, np.pi / 2, na + 1)
            theta_a = np.linspace(np.pi / 2, t_a, na + 1)
            theta_aa = np.linspace(t_aa, np.pi / 2, na + 1)
            theta_b1 = np.linspace(kp_12_angle, t_f, nf + 1)
            theta_b2 = np.linspace(t_ff, kp_14_angle, nf + 1)
            line = [
                np.linspace(kp_0[..., :-1], kp_1[..., :-1], n3 + 1),
                points[n1 + n2 + 1:2 * n1 + n2 + 2, :-1],
                points[2 * n1 + n2 + 1:2 * n1 + 2 * n2 + 2,
                :-1],
                np.linspace(kp_10[..., :-1], kp_7[..., :-1], n3 + 1),
                np.linspace(kp_7[..., :-1], kp_8[..., :-1], n1 + 1),
                np.linspace(kp_8[..., :-1], kp_9[..., :-1], n2 + 1),
                np.linspace(kp_11[..., :-1], kp_4[..., :-1], n3 + 1),
                points[:n1 + 1, :-1],
                points[n1:n1 + n2 + 1, :-1],
                np.concatenate([r_inner * np.cos(theta_f)[:, None], r_inner * np.sin(theta_f)[:, None]], axis=1),
                np.linspace(kp_7[..., :-1], kp_1[..., :-1], na + 1),
                np.linspace(kp_8[..., :-1], kp_2[..., :-1], na + 1),
                np.concatenate([ra * np.cos(theta_a)[:, None], ra * np.sin(theta_a)[:, None]], axis=1),
                np.concatenate([r_inner * np.cos(theta_ff)[:, None], r_inner * np.sin(theta_ff)[:, None]], axis=1),
                np.linspace(kp_4[..., :-1], kp_7[..., :-1], na + 1),
                np.linspace(kp_5[..., :-1], kp_8[..., :-1], na + 1),
                np.concatenate([ra * np.cos(theta_aa)[:, None], ra * np.sin(theta_aa)[:, None]], axis=1),
                np.linspace(kp_12[..., :-1], kp_13[..., :-1], n3 + 1),
                np.linspace(kp_14[..., :-1], kp_15[..., :-1], n3 + 1),
                np.concatenate([r_inner * np.cos(theta_b1)[:, None], r_inner * np.sin(theta_b1)[:, None]], axis=1),
                np.concatenate([rf * np.cos(theta_b1)[:, None], rf * np.sin(theta_b1)[:, None]], axis=1),
                np.concatenate([r_inner * np.cos(theta_b2)[:, None], r_inner * np.sin(theta_b2)[:, None]], axis=1),
                np.concatenate([rf * np.cos(theta_b2)[:, None], rf * np.sin(theta_b2)[:, None]], axis=1)
            ]
            # 单齿网格及其节点与单元
            quad_mesh = QuadrangleMesh.sub_domain_mesh_generator(half_edge, key_points[:, :-1], line)
            tooth_node = quad_mesh.node
            tooth_cell = quad_mesh.cell
            origin_cell = quad_mesh.cell
            # 旋转构建剩余点与单元，并依次拼接
            single_node_num = len(tooth_node) - (n3 + 1)
            temp_node = np.concatenate(
                [tooth_node[:12], tooth_node[14:len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))],
                 tooth_node[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1)):]], axis=0)
            # 最后一个齿的节点，需要特殊处理
            temp_node_last = np.concatenate(
                [tooth_node[:12], tooth_node[16:len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))],
                 tooth_node[len(key_points) + edge_node_num - (4 * (nf - 1)):]], axis=0)
            # 辅助所用的节点映射，将新节点编号按照初始单元节点排列
            origin_trans_matrix = np.arange(len(tooth_node))
            trans_matrix = np.arange(len(tooth_node))
            # 左侧齿
            # 处理重复顶点
            trans_matrix[12] = trans_matrix[14]
            trans_matrix[13] = trans_matrix[15]
            # 处理重复边上节点
            trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))
                         :len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))] \
                = trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))
                               :len(key_points) + edge_node_num - (4 * (nf - 1))]
            # 其他节点
            trans_matrix[0:12] += single_node_num + (n3 - 1) + 2
            trans_matrix[14:len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))] += single_node_num + (
                    n3 - 1)
            trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1)):] += single_node_num
            # 计算新节点与单元
            rot_matrix = np.array([[np.cos(rot_phi[1]), -np.sin(rot_phi[1])], [np.sin(rot_phi[1]), np.cos(rot_phi[1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
            new_cell = trans_matrix[origin_cell]
            # 拼接
            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            # 中间齿
            for i in range(2, z - 1):
                rot_matrix = np.array(
                    [[np.cos(rot_phi[i]), -np.sin(rot_phi[i])], [np.sin(rot_phi[i]), np.cos(rot_phi[i])]])
                new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
                # 处理重复顶点
                trans_matrix[12] = trans_matrix[14]
                trans_matrix[13] = trans_matrix[15]
                # 处理重复边上节点
                trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))
                             :len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))] \
                    = trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))
                                   :len(key_points) + edge_node_num - (4 * (nf - 1))]
                # 其他节点
                trans_matrix[0:12] += single_node_num
                trans_matrix[14:len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))] += single_node_num
                trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1)):] += single_node_num
                # 新单元映射与拼接
                new_cell = trans_matrix[origin_cell]
                tooth_node = np.concatenate([tooth_node, new_node], axis=0)
                tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            # 右侧齿
            rot_matrix = np.array(
                [[np.cos(rot_phi[-1]), -np.sin(rot_phi[-1])], [np.sin(rot_phi[-1]), np.cos(rot_phi[-1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node_last.T).T
            # 处理重复顶点
            trans_matrix[12] = trans_matrix[14]
            trans_matrix[13] = trans_matrix[15]
            trans_matrix[14] = origin_trans_matrix[12]
            trans_matrix[15] = origin_trans_matrix[13]
            # 处理重复边上节点
            trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))
                         :len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))] \
                = trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))
                               :len(key_points) + edge_node_num - (4 * (nf - 1))]
            trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))
                         :len(key_points) + edge_node_num - (4 * (nf - 1))] \
                = origin_trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))
                                      :len(key_points) + edge_node_num - (4 * (nf - 1) + (n3 - 1))]
            # 其他节点
            trans_matrix[0:12] += single_node_num
            trans_matrix[16:len(key_points) + edge_node_num - (4 * (nf - 1) + 2 * (n3 - 1))] += single_node_num - 2
            trans_matrix[len(key_points) + edge_node_num - (4 * (nf - 1)):] += single_node_num - (n3 - 1) - 2
            # 新单元映射与拼接
            new_cell = trans_matrix[origin_cell]
            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            # 最终网格
            t_mesh = QuadrangleMesh(tooth_node, tooth_cell)

        self.mesh = t_mesh
        return t_mesh


class InternalGear(Gear):
    def __init__(self, m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf, outer_diam, z_cutter, xn_cutter):
        """

        @param m_n: 法向模数
        @param z: 齿数
        @param alpha_n: 法向压力角
        @param beta: 螺旋角
        @param x_n: 法向变位系数
        @param hac: 齿顶高系数
        @param cc: 顶隙系数
        @param rcc: 刀尖圆弧半径系数
        @param jn: 法向侧隙
        @param n1: 渐开线分段数
        @param n2: 过渡曲线分段数
        @param n3: 齿轮内部分段数
        @param na: 齿顶分段数
        @param nf: 齿根圆部分分段数（一侧，非最大圆角时）
        @param outter_diam: 轮缘外径
        @param z_cutter: 刀具齿数
        @param xn_cutter: 刀具变位系数
        """
        super().__init__(m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf)
        self.outer_diam = outer_diam
        self.z_cutter = z_cutter
        self.xn_cutter = xn_cutter
        # 齿顶圆直径与半径
        ha = self.m_n * (self.hac - self.x_n)  # TODO: 确定此处使用的端面还是法向变位系数
        self.d_a = self.d - 2 * ha
        self.r_a = self.d_a/2
        # 齿根圆直径与半径
        hf = self.m_n * (self.hac + self.cc + self.x_n)
        self.d_f = self.d + 2 * hf
        self.r_f = self.d_f / 2
        # 刀具分度圆直径与半径
        self.d_cutter = self.m_t*self.z_cutter
        self.r_cutter = self.d_cutter/2
        # 刀具基圆直径与半径
        self.db_cutter = self.d_cutter*cos(self.alpha_t)
        self.rb_cutter = self.db_cutter/2
        # 刀具齿顶圆直径与半径
        ha_cutter = self.m_n*(self.hac + self.cc + self.xn_cutter)
        self.da_cutter = self.d_cutter+2*ha_cutter
        self.ra_cutter = self.da_cutter/2
        # 刀具齿根圆直径与半径
        hf_cutter = self.m_n*(self.hac - self.xn_cutter)
        self.df_cutter = self.d_cutter - 2 * hf_cutter
        self.rf_cutter = self.df_cutter / 2
        # 刀具齿槽半角
        eta = (pi - 4 * self.xn_cutter * tan(self.alpha_n)) / (2 * self.z_cutter)
        self.etab = pi / self.z_cutter - (eta - (tan(self.alpha_t) - self.alpha_t))
        # 刀尖圆弧半径
        self.rc = self.m_n*self.rcc
        # 相关参数计算
        etab = self.etab
        func = lambda t: [
            self.rb_cutter * cos(etab) * (sin(t[0]) - t[0] * cos(t[0])) - self.rb_cutter * sin(etab) * (cos(t[0]) + t[0] * sin(t[0])) - t[
                2] * cos(t[1]),
            self.rb_cutter * cos(etab) * (cos(t[0]) + t[0] * sin(t[0])) + self.rb_cutter * sin(etab) * (sin(t[0]) - t[0] * cos(t[0])) - (
                    t[2] * sin(t[1]) + self.ra_cutter - t[2]),
            (self.rb_cutter * t[0] * sin(etab) * sin(t[0]) + self.rb_cutter * t[0] * cos(etab) * cos(t[0])) / (
                    self.rb_cutter * t[0] * cos(etab) * sin(t[0]) - self.rb_cutter * t[0] * cos(t[0]) * sin(etab)) + cos(t[1]) / sin(t[1])
        ]
        self.t = fsolve(func, [1, 0.75 * pi, 0.25 * self.m_n])

    @classmethod
    def ainv(cls, x):
        temp = 0
        alpha = arctan(x)
        while np.abs(alpha - temp) > 1e-25:
            temp = alpha
            alpha = np.arctan(x + temp)
        return alpha

    def get_involute_points(self, t):
        alphan = self.alpha_n
        alphat = self.alpha_t
        rb = self.r_b
        xn = self.x_n
        z = self.z

        eta = (pi - 4 * xn * np.tan(alphan)) / (2 * z)
        etab = pi / z - (eta - (tan(alphat) - alphat))
        xt = (rb * cos(etab) * (sin(t) - t * cos(t)) - rb * sin(etab) * (cos(t) + t * sin(t))).reshape((-1, 1))
        yt = (rb * cos(etab) * (cos(t) + t * sin(t)) + rb * sin(etab) * (sin(t) - t * cos(t))).reshape((-1, 1))

        points = np.concatenate([xt, yt], axis=1)
        return points

    def get_tip_intersection_points(self, t):

        points = self.get_involute_points(t)
        return np.sqrt(points[..., 0] ** 2 + points[..., 1] ** 2)

    def get_transition_points(self, E, x0, y0, rc, ratio, t):

        def calc_phi(t_values):
            def f(phi, tt):
                cos_phi = cos(phi * (ratio - 1))
                sin_phi = sin(phi * (ratio - 1))
                term1 = -(rc * cos_phi * cos(tt) + rc * sin_phi * sin(tt)) * \
                        (E * cos(phi) + sin_phi * (x0 + rc * cos(tt)) * (ratio - 1) - \
                         cos_phi * (y0 + rc * sin(tt)) * (ratio - 1))
                term2 = -(rc * cos_phi * sin(tt) - rc * sin_phi * cos(tt)) * \
                        (E * sin(phi) + cos_phi * (x0 + rc * cos(tt)) * (ratio - 1) + \
                         sin_phi * (y0 + rc * sin(tt)) * (ratio - 1))
                return term1 + term2

            phi_values = []
            for tt in t_values:
                phi = fsolve(f, 0, args=(tt))[0]  # 对每个 tt 调用 fsolve
                phi_values.append(phi)

            return np.array(phi_values)

        phi = calc_phi(t)
        xt = (sin(phi * (ratio - 1)) * (y0 + rc * sin(t)) - E * sin(phi) + cos(phi * (ratio - 1)) * (x0 + rc * cos(t))).reshape((-1, 1))
        yt = (E * cos(phi) - sin(phi * (ratio - 1)) * (x0 + rc * cos(t)) + cos(phi * (ratio - 1)) * (y0 + rc * sin(t))).reshape((-1, 1))

        points = np.concatenate([xt, yt], axis=1)
        return points

    def get_profile_points(self):
        ra_cutter = self.ra_cutter
        rb_cutter = self.rb_cutter
        t = self.t
        rc = self.rc
        n1 = self.n1
        n2 = self.n2
        n3 = self.n3
        na = self.na
        etab = self.etab

        ratio = self.z / self.z_cutter
        alphawt = InternalGear.ainv(
            2 * (self.x_n - self.xn_cutter) * tan(self.alpha_n) / (self.z - self.z_cutter) + (tan(self.alpha_t) - self.alpha_t))
        E = 0.5 * (self.d - self.d_cutter) + self.m_t * (0.5 * (self.z - self.z_cutter) * (cos(self.alpha_t) / cos(alphawt) - 1))
        df11 = 2 * (E + ra_cutter)

        if rc >= t[2]:
            points = np.zeros((2 * (n1 + n2) + 1, 3))
            x0 = 0
            y0 = ra_cutter - rc
            t2 = t[1]
            jb = (t[1] - pi / 2) / n2
            tt = np.linspace(t[1], pi/2, n2, endpoint=False)
            points[n1:n1+n2, 0:2] = self.get_transition_points(E, x0, y0, rc, ratio, tt)

            # 中点
            points[n1 + n2, 0] = 0
            points[n1 + n2, 1] = 0.5 * df11

            func2 = lambda t: self.get_tip_intersection_points(t) - sqrt(
                points[n1, 0] ** 2 + points[n1, 1] ** 2)
            t2 = fsolve(func2, 1)[0]
            func1 = lambda t: self.get_tip_intersection_points(t) - 0.5 * self.d_a
            t1 = fsolve(func1, 1)[0]
            tt = np.linspace(t1, t2, n1, endpoint=False)
            points[:n1, 0:2] = self.get_involute_points(tt)

            # 对称构造另一侧点
            points[n1+n2+1:, 0] = -points[0:n1+n2, 0][::-1]
            points[n1+n2+1:, 1] = points[0:n1+n2, 1][::-1]
        else:
            nf = self.nf
            points = np.zeros((2 * (n1 + n2 + nf) + 1, 3))
            func = lambda t: [
                rb_cutter * cos(etab) * (sin(t[0]) - t[0] * cos(t[0])) - rb_cutter * sin(etab) * (
                        cos(t[0]) + t[0] * sin(t[0])) - (
                        rc * cos(t[1]) + t[2]),
                rb_cutter * cos(etab) * (cos(t[0]) + t[0] * sin(t[0])) + rb_cutter * sin(etab) * (
                        sin(t[0]) - t[0] * cos(t[0])) - (
                        rc * sin(t[1]) + t[3]),
                (rb_cutter * t[0] * sin(etab) * sin(t[0]) + rb_cutter * t[0] * cos(etab) * cos(t[0])) / (
                        rb_cutter * t[0] * cos(etab) * sin(t[0]) - rb_cutter * t[0] * cos(t[0]) * sin(etab)) + cos(t[1]) / sin(
                    t[1]),
                t[2] ** 2 + t[3] ** 2 - (ra_cutter - rc) ** 2
            ]

            t = fsolve(func, [1, 0.75 * pi, 0, ra_cutter])
            self.t = t
            x0 = t[2]
            y0 = t[3]
            t3 = pi / 2 - arctan(x0 / y0)
            t4 = t[1]

            tt = np.linspace(t4, t3, n2, endpoint=False)
            points[n1+1:n1+n2+1, 0:2] = self.get_transition_points(E, x0, y0, rc, ratio, tt)

            t5 = pi / 2 - arctan(x0 / y0)
            t6 = pi / 2
            tt = np.linspace(t5, t6, nf-1, endpoint=False)
            points[n1 + n2 + 1:n1 + n2 + nf, 0:2] = self.get_transition_points(E, 0, 0, ra_cutter, ratio, tt)

            points[n1 + n2 + nf, 0] = 0
            points[n1 + n2 + nf, 1] = 0.5 * df11

            func2 = lambda t: self.get_tip_intersection_points(t) - sqrt(
                points[n1 + 1, 0] ** 2 + points[n1 + 1, 1] ** 2)
            t2 = fsolve(func2, 1)[0]

            func1 = lambda t: self.get_tip_intersection_points(t) - 0.5 * self.d_a
            t1 = fsolve(func1, 1)[0]

            tt = np.linspace(t1, t2, n1, endpoint=False)
            points[0:n1, 0:2] = self.get_involute_points(tt)

            points[n1, :] = (points[n1 - 1, :] + points[n1 + 1, :]) / 2

            points[n1+n2+nf+1:, 0] = -points[0:n1+n2+nf, 0][::-1]
            points[n1+n2+nf+1:, 1] = points[0:n1+n2+nf, 1][::-1]

        return points

    def generate_mesh(self):
        rc = self.rc
        t = self.t
        z = self.z
        ra = self.r_a
        n1 = self.n1
        n2 = self.n2
        n3 = self.n3
        na = self.na
        nf = self.nf

        if rc >= t[2]:
            points = self.get_profile_points()
            # 构建关键点
            phi00 = pi / 2 - 2 * pi / z / 2
            phi01 = pi / 2 + 2 * pi / z / 2
            t1 = (self.r_f - ra) / (outer_diam / 2 - ra) * 1.236
            t2 = 0.618 * t1

            kp0 = ra * np.array([cos(phi00), sin(phi00)]).reshape(1, -1)
            kp3 = outer_diam / 2 * np.array([cos(phi00), sin(phi00)]).reshape(1, -1)
            kp1 = (1 - t2) * kp0 + t2 * kp3
            kp2 = (1 - t1) * kp0 + t1 * kp3

            kp4 = np.zeros_like(kp0)
            kp4[:, 0] = -kp0[:, 0]
            kp4[:, 1] = kp0[:, 1]
            kp5 = np.zeros_like(kp0)
            kp5[:, 0] = -kp1[:, 0]
            kp5[:, 1] = kp1[:, 1]
            kp6 = np.zeros_like(kp0)
            kp6[:, 0] = -kp2[:, 0]
            kp6[:, 1] = kp2[:, 1]
            kp7 = np.zeros_like(kp0)
            kp7[:, 0] = -kp3[:, 0]
            kp7[:, 1] = kp3[:, 1]

            kp10 = points[0:1, 0:2]
            kp11 = points[n1:n1 + 1, 0:2]
            kp8 = points[-1:, 0:2]
            kp9 = points[n1 + 2 * n2:n1 + 2 * n2 + 1, 0:2]

            kp12 = points[n1 + n2:n1 + n2 + 1, 0:2]

            kp13 = np.array([0, outer_diam / 2]).reshape((1, -1))

            key_points = np.concatenate(
                [kp0, kp1, kp2, kp3, kp4, kp5, kp6, kp7, kp8, kp9, kp10, kp11, kp12, kp13], axis=0)

            # 构造 edge 与 line
            edge = np.array([[0, 1],
                             [1, 2],
                             [2, 3],
                             [4, 5],
                             [5, 6],
                             [6, 7],
                             [8, 9],
                             [9, 12],
                             [10, 11],
                             [11, 12],
                             [8, 0],
                             [9, 1],
                             [12, 2],
                             [13, 3],
                             [4, 10],
                             [5, 11],
                             [6, 12],
                             [7, 13],
                             [12, 13]])

            phi20 = arctan2(kp8[:, 1], kp8[:, 0])
            phi21 = arctan2(kp10[:, 1], kp10[:, 0])
            delta00 = np.linspace(phi20, phi00, na + 1)
            delta01 = np.linspace(phi01, phi21, na + 1)
            delta10 = np.linspace(pi / 2, phi00, na + 1).reshape((-1, 1))
            delta11 = np.linspace(phi01, pi / 2, na + 1).reshape((-1, 1))
            line = [
                np.linspace(key_points[edge[0, 0]], key_points[edge[0, 1]], n1 + 1),
                np.linspace(key_points[edge[1, 0]], key_points[edge[1, 1]], n2 + 1),
                np.linspace(key_points[edge[2, 0]], key_points[edge[2, 1]], n3 + 1),
                np.linspace(key_points[edge[3, 0]], key_points[edge[3, 1]], n1 + 1),
                np.linspace(key_points[edge[4, 0]], key_points[edge[4, 1]], n2 + 1),
                np.linspace(key_points[edge[5, 0]], key_points[edge[5, 1]], n3 + 1),
                points[n1 + 2 * n2:, :-1][::-1],
                points[n1 + n2:n1 + 2 * n2 + 1, :-1][::-1],
                points[0:n1 + 1, :-1],
                points[n1:n1 + n2 + 1, :-1],
                np.concatenate([ra * cos(delta00), ra * sin(delta00)], axis=1),
                np.linspace(key_points[edge[11, 0]], key_points[edge[11, 1]], na + 1),
                np.linspace(key_points[edge[12, 0]], key_points[edge[12, 1]], na + 1),
                np.concatenate([outer_diam / 2 * cos(delta10), outer_diam / 2 * sin(delta10)], axis=1),
                np.concatenate([ra * cos(delta01), ra * sin(delta01)], axis=1),
                np.linspace(key_points[edge[15, 0]], key_points[edge[15, 1]], na + 1),
                np.linspace(key_points[edge[16, 0]], key_points[edge[16, 1]], na + 1),
                np.concatenate([outer_diam / 2 * cos(delta11), outer_diam / 2 * sin(delta11)], axis=1),
                np.linspace(key_points[edge[18, 0]], key_points[edge[18, 1]], n3 + 1)
            ]

            # 构建子区域半边数据结构
            half_edge = np.zeros((len(edge) * 2, 5), dtype=np.int64)
            half_edge[::2, 0] = edge[:, 1]
            half_edge[1::2, 0] = edge[:, 0]

            half_edge[::2, 4] = 2 * np.arange(len(edge)) + 1
            half_edge[1::2, 4] = 2 * np.arange(len(edge))

            half_edge[np.array([0, 1, 2]) * 2, 1] = np.array([0, 1, 2])
            half_edge[np.array([0, 1, 2]) * 2 + 1, 1] = -1
            half_edge[np.array([3, 4, 5]) * 2, 1] = -1
            half_edge[np.array([3, 4, 5]) * 2 + 1, 1] = np.array([3, 4, 5])
            half_edge[np.array([6, 7]) * 2, 1] = -1
            half_edge[np.array([6, 7]) * 2 + 1, 1] = np.array([0, 1])
            half_edge[np.array([8, 9]) * 2, 1] = np.array([3, 4])
            half_edge[np.array([8, 9]) * 2 + 1, 1] = -1
            half_edge[np.array([10, 14]) * 2, 1] = np.array([0, 3])
            half_edge[np.array([10, 14]) * 2 + 1, 1] = -1
            half_edge[np.array([13, 17]) * 2, 1] = -1
            half_edge[np.array([13, 17]) * 2 + 1, 1] = np.array([2, 5])
            half_edge[np.array([11, 12, 15, 16]) * 2, 1] = np.array([1, 2, 4, 5])
            half_edge[np.array([11, 12, 15, 16]) * 2 + 1, 1] = np.array([0, 1, 3, 4])
            half_edge[18 * 2, 1] = 5
            half_edge[18 * 2 + 1, 1] = 2

            half_edge[::2, 2] = np.array(
                [23, 25, 27, 8, 10, 34, 14, 19, 31, 33, 0, 2, 4, 5, 16, 18, 36, 26, 35])
            half_edge[1::2, 2] = np.array(
                [21, 1, 3, 28, 30, 32, 20, 22, 29, 17, 12, 13, 15, 37, 6, 7, 9, 11, 24])

            half_edge[::2, 3] = np.array(
                [20, 22, 24, 29, 6, 8, 21, 12, 28, 30, 13, 15, 37, 34, 7, 9, 11, 10, 32])
            half_edge[1::2, 3] = np.array(
                [3, 5, 26, 31, 33, 35, 23, 25, 19, 14, 1, 0, 2, 4, 17, 16, 18, 36, 27])

            quad_mesh = QuadrangleMesh.sub_domain_mesh_generator(half_edge, key_points, line)
            tooth_node = quad_mesh.node
            tooth_cell = quad_mesh.cell
            origin_cell = quad_mesh.cell

            # 旋转角
            rot_phi = np.linspace(0, 2 * np.pi, z, endpoint=False)
            phi = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)

            # 生成完整内齿
            edge_node_num = 4 * (n1 + n2 - 2) + 8 * (na - 1) + 3 * (n3 - 1)
            single_node_num = len(tooth_node) - (n1 + n2 + n3 + 1)
            single_cell_num = len(tooth_cell)
            temp_node = np.concatenate(
                [tooth_node[4:len(key_points)], tooth_node[len(key_points) + (n1 + n2 + n3 - 3):]], axis=0)
            temp_node_last = np.concatenate(
                [tooth_node[8:len(key_points)], tooth_node[len(key_points) + 2 * (n1 + n2 + n3 - 3):]], axis=0)

            origin_trans_matrix = np.arange(len(tooth_node))
            trans_matrix = np.arange(len(tooth_node))
            # 左侧齿
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[4]
            trans_matrix[1] = trans_matrix[5]
            trans_matrix[2] = trans_matrix[6]
            trans_matrix[3] = trans_matrix[7]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]

            # 其他节点
            trans_matrix[4:len(key_points)] += single_node_num + (n1 + n2 + n3 - 3)
            trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):] += single_node_num

            rot_matrix = np.array([[np.cos(rot_phi[1]), -np.sin(rot_phi[1])], [np.sin(rot_phi[1]), np.cos(rot_phi[1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
            new_cell = trans_matrix[origin_cell]

            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)
            t_mesh = QuadrangleMesh(tooth_node, tooth_cell)

            for i in range(2, z - 1):
                rot_matrix = np.array(
                    [[np.cos(rot_phi[i]), -np.sin(rot_phi[i])], [np.sin(rot_phi[i]), np.cos(rot_phi[i])]])
                new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T

                # 处理重复顶点
                trans_matrix[0] = trans_matrix[4]
                trans_matrix[1] = trans_matrix[5]
                trans_matrix[2] = trans_matrix[6]
                trans_matrix[3] = trans_matrix[7]
                # 处理重复边上节点
                trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                    = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]
                # 其他节点
                trans_matrix[4:len(key_points)] += single_node_num
                trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):] += single_node_num

                new_cell = trans_matrix[origin_cell]
                tooth_node = np.concatenate([tooth_node, new_node], axis=0)
                tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            # 右侧齿
            rot_matrix = np.array(
                [[np.cos(rot_phi[-1]), -np.sin(rot_phi[-1])], [np.sin(rot_phi[-1]), np.cos(rot_phi[-1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node_last.T).T
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[4]
            trans_matrix[1] = trans_matrix[5]
            trans_matrix[2] = trans_matrix[6]
            trans_matrix[3] = trans_matrix[7]
            trans_matrix[4] = origin_trans_matrix[0]
            trans_matrix[5] = origin_trans_matrix[1]
            trans_matrix[6] = origin_trans_matrix[2]
            trans_matrix[7] = origin_trans_matrix[3]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]
            trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)] \
                = origin_trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)]

            # 其他节点
            trans_matrix[8:len(key_points)] += single_node_num - 4
            trans_matrix[len(key_points) + 2 * (n1 + n2 + n3 - 3):] += single_node_num - (n1 + n2 + n3 + 1)

            new_cell = trans_matrix[origin_cell]
            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            t_mesh = QuadrangleMesh(tooth_node, tooth_cell)
            self.mesh = t_mesh
            return t_mesh
        else:
            points = self.get_profile_points()
            # 构建关键点
            phi00 = pi / 2 - 2 * pi / z / 2
            phi01 = pi / 2 + 2 * pi / z / 2
            t1 = (self.r_f - ra) / (outer_diam / 2 - ra) * 1.236
            t2 = 0.618 * t1

            kp0 = ra * np.array([cos(phi00), sin(phi00)]).reshape(1, -1)
            kp3 = outer_diam / 2 * np.array([cos(phi00), sin(phi00)]).reshape(1, -1)
            kp1 = (1 - t2) * kp0 + t2 * kp3
            kp2 = (1 - t1) * kp0 + t1 * kp3

            kp4 = np.zeros_like(kp0)
            kp4[:, 0] = -kp0[:, 0]
            kp4[:, 1] = kp0[:, 1]
            kp5 = np.zeros_like(kp0)
            kp5[:, 0] = -kp1[:, 0]
            kp5[:, 1] = kp1[:, 1]
            kp6 = np.zeros_like(kp0)
            kp6[:, 0] = -kp2[:, 0]
            kp6[:, 1] = kp2[:, 1]
            kp7 = np.zeros_like(kp0)
            kp7[:, 0] = -kp3[:, 0]
            kp7[:, 1] = kp3[:, 1]

            kp10 = points[0:1, 0:2]
            kp11 = points[n1:n1 + 1, 0:2]
            kp16 = points[n1 + n2:n1 + n2 + 1, 0:2]
            kp12 = points[n1 + n2 + nf:n1 + n2 + nf + 1, 0:2]
            kp8 = points[-1:, 0:2]
            kp9 = points[n1 + 2 * n2 + 2 * nf:n1 + 2 * n2 + 2 * nf + 1, 0:2]
            kp14 = points[n1 + n2 + 2 * nf:n1 + n2 + 2 * nf + 1, 0:2]

            kp13 = np.array([0, outer_diam / 2]).reshape((1, -1))

            phi10 = arctan2(kp14[:, 1], kp14[:, 0])
            phi11 = arctan2(kp16[:, 1], kp16[:, 0])
            kp15 = outer_diam / 2 * np.array([cos(phi10), sin(phi10)]).reshape(1, -1)
            kp17 = outer_diam / 2 * np.array([cos(phi11), sin(phi11)]).reshape(1, -1)

            key_points = np.concatenate(
                [kp0, kp1, kp2, kp3, kp4, kp5, kp6, kp7, kp8, kp9, kp10, kp11, kp12, kp13, kp14, kp15, kp16, kp17],
                axis=0)
            # 构造 edge 与 line
            edge = np.array([[0, 1],
                             [1, 2],
                             [2, 3],
                             [4, 5],
                             [5, 6],
                             [6, 7],
                             [8, 9],
                             [9, 14],
                             [10, 11],
                             [11, 16],
                             [8, 0],
                             [9, 1],
                             [14, 2],
                             [15, 3],
                             [4, 10],
                             [5, 11],
                             [6, 16],
                             [7, 17],
                             [14, 15],
                             [12, 13],
                             [16, 17],
                             [12, 14],
                             [16, 12],
                             [13, 15],
                             [17, 13]])
            phi20 = arctan2(kp8[:, 1], kp8[:, 0])
            phi21 = arctan2(kp10[:, 1], kp10[:, 0])
            delta00 = np.linspace(phi20, phi00, na+1)
            delta01 = np.linspace(phi01, phi21, na+1)
            delta10 = np.linspace(phi10, phi00, na+1)
            delta11 = np.linspace(phi01, phi11, na+1)
            delta20 = np.linspace(pi / 2, phi10, nf + 1)
            delta21 = np.linspace(phi11, pi / 2, nf + 1)
            line = [
                np.linspace(key_points[edge[0, 0]], key_points[edge[0, 1]], n1 + 1),
                np.linspace(key_points[edge[1, 0]], key_points[edge[1, 1]], n2 + 1),
                np.linspace(key_points[edge[2, 0]], key_points[edge[2, 1]], n3 + 1),
                np.linspace(key_points[edge[3, 0]], key_points[edge[3, 1]], n1 + 1),
                np.linspace(key_points[edge[4, 0]], key_points[edge[4, 1]], n2 + 1),
                np.linspace(key_points[edge[5, 0]], key_points[edge[5, 1]], n3 + 1),
                points[n1 + 2 * n2 + 2 * nf:, :-1][::-1],
                points[n1 + n2 + 2 * nf:n1 + 2 * n2 + 2 * nf + 1, :-1][::-1],
                points[0:n1 + 1, :-1],
                points[n1:n1 + n2 + 1, :-1],
                np.concatenate([ra * cos(delta00), ra * sin(delta00)], axis=1),
                np.linspace(key_points[edge[11, 0]], key_points[edge[11, 1]], na + 1),
                np.linspace(key_points[edge[12, 0]], key_points[edge[12, 1]], na + 1),
                np.concatenate([outer_diam/2 * cos(delta10), outer_diam/2 * sin(delta10)], axis=1),
                np.concatenate([ra * cos(delta01), ra * sin(delta01)], axis=1),
                np.linspace(key_points[edge[15, 0]], key_points[edge[15, 1]], na + 1),
                np.linspace(key_points[edge[16, 0]], key_points[edge[16, 1]], na + 1),
                np.concatenate([outer_diam / 2 * cos(delta11), outer_diam / 2 * sin(delta11)], axis=1),
                np.linspace(key_points[edge[18, 0]], key_points[edge[18, 1]], n3 + 1),
                np.linspace(key_points[edge[19, 0]], key_points[edge[19, 1]], n3 + 1),
                np.linspace(key_points[edge[20, 0]], key_points[edge[20, 1]], n3 + 1),
                points[n1 + n2 + nf:n1 + n2 + 2 * nf + 1, :-1],
                points[n1 + n2:n1 + n2 + nf + 1, :-1],
                np.concatenate([outer_diam / 2 * cos(delta20), outer_diam / 2 * sin(delta20)], axis=1),
                np.concatenate([outer_diam / 2 * cos(delta21), outer_diam / 2 * sin(delta21)], axis=1),
            ]
            half_edge = np.zeros((len(edge) * 2, 5), dtype=np.int64)
            half_edge[::2, 0] = edge[:, 1]
            half_edge[1::2, 0] = edge[:, 0]

            half_edge[::2, 4] = 2 * np.arange(len(edge)) + 1
            half_edge[1::2, 4] = 2 * np.arange(len(edge))

            half_edge[np.array([0, 1, 2]) * 2, 1] = np.array([0, 1, 2])
            half_edge[np.array([0, 1, 2]) * 2 + 1, 1] = -1
            half_edge[np.array([3, 4, 5]) * 2, 1] = -1
            half_edge[np.array([3, 4, 5]) * 2 + 1, 1] = np.array([3, 4, 5])
            half_edge[np.array([6, 7]) * 2, 1] = -1
            half_edge[np.array([6, 7]) * 2 + 1, 1] = np.array([0, 1])
            half_edge[np.array([8, 9]) * 2, 1] = np.array([3, 4])
            half_edge[np.array([8, 9]) * 2 + 1, 1] = -1
            half_edge[np.array([10, 14]) * 2, 1] = np.array([0, 3])
            half_edge[np.array([10, 14]) * 2 + 1, 1] = -1
            half_edge[np.array([13, 17]) * 2, 1] = -1
            half_edge[np.array([13, 17]) * 2 + 1, 1] = np.array([2, 5])
            half_edge[np.array([11, 12, 15, 16]) * 2, 1] = np.array([1, 2, 4, 5])
            half_edge[np.array([11, 12, 15, 16]) * 2 + 1, 1] = np.array([0, 1, 3, 4])
            half_edge[np.array([18, 19, 20]) * 2, 1] = np.array([6, 7, 5])
            half_edge[np.array([18, 19, 20]) * 2 + 1, 1] = np.array([2, 6, 7])
            half_edge[np.array([21, 22]) * 2, 1] = np.array([6, 7])
            half_edge[np.array([21, 22]) * 2 + 1, 1] = -1
            half_edge[np.array([23, 24]) * 2, 1] = -1
            half_edge[np.array([23, 24]) * 2 + 1, 1] = np.array([6, 7])

            half_edge[::2, 2] = np.array(
                [23, 25, 27, 8, 10, 34, 14, 43, 31, 33, 0, 2, 4, 5, 16, 18, 40, 48, 47, 49, 35, 36, 38, 26, 46])
            half_edge[1::2, 2] = np.array(
                [21, 1, 3, 28, 30, 32, 20, 22, 29, 17, 12, 13, 15, 37, 6, 7, 9, 11, 24, 42, 44, 45, 19, 39, 41])

            half_edge[::2, 3] = np.array(
                [20, 22, 24, 29, 6, 8, 21, 12, 28, 30, 13, 15, 37, 46, 7, 9, 11, 10, 42, 44, 32, 39, 41, 48, 34])
            half_edge[1::2, 3] = np.array(
                [3, 5, 26, 31, 33, 35, 23, 25, 19, 45, 1, 0, 2, 4, 17, 16, 18, 40, 27, 47, 49, 14, 43, 36, 38])
            quad_mesh = QuadrangleMesh.sub_domain_mesh_generator(half_edge, key_points, line)
            tooth_node = quad_mesh.node
            tooth_cell = quad_mesh.cell
            origin_cell = quad_mesh.cell

            # 旋转角
            rot_phi = np.linspace(0, 2 * np.pi, z, endpoint=False)
            phi = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)

            # 生成完整内齿
            edge_node_num = 4 * (n1 + n2 + nf - 3) + 8 * (na - 1) + 5 * (n3 - 1)
            single_node_num = len(tooth_node) - (n1 + n2 + n3 + 1)
            single_cell_num = len(tooth_cell)
            temp_node = np.concatenate(
                [tooth_node[4:len(key_points)], tooth_node[len(key_points) + (n1 + n2 + n3 - 3):]], axis=0)
            temp_node_last = np.concatenate(
                [tooth_node[8:len(key_points)], tooth_node[len(key_points) + 2 * (n1 + n2 + n3 - 3):]], axis=0)
            origin_trans_matrix = np.arange(len(tooth_node))
            trans_matrix = np.arange(len(tooth_node))
            # 左侧齿
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[4]
            trans_matrix[1] = trans_matrix[5]
            trans_matrix[2] = trans_matrix[6]
            trans_matrix[3] = trans_matrix[7]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]

            # 其他节点
            trans_matrix[4:len(key_points)] += single_node_num + (n1 + n2 + n3 - 3)
            trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):] += single_node_num

            rot_matrix = np.array([[np.cos(rot_phi[1]), -np.sin(rot_phi[1])], [np.sin(rot_phi[1]), np.cos(rot_phi[1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T
            new_cell = trans_matrix[origin_cell]

            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            for i in range(2, z - 1):
                rot_matrix = np.array(
                    [[np.cos(rot_phi[i]), -np.sin(rot_phi[i])], [np.sin(rot_phi[i]), np.cos(rot_phi[i])]])
                new_node = np.einsum('ij,jn->in', rot_matrix, temp_node.T).T

                # 处理重复顶点
                trans_matrix[0] = trans_matrix[4]
                trans_matrix[1] = trans_matrix[5]
                trans_matrix[2] = trans_matrix[6]
                trans_matrix[3] = trans_matrix[7]
                # 处理重复边上节点
                trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                    = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]
                # 其他节点
                trans_matrix[4:len(key_points)] += single_node_num
                trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):] += single_node_num

                new_cell = trans_matrix[origin_cell]
                tooth_node = np.concatenate([tooth_node, new_node], axis=0)
                tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            # 右侧齿
            rot_matrix = np.array(
                [[np.cos(rot_phi[-1]), -np.sin(rot_phi[-1])], [np.sin(rot_phi[-1]), np.cos(rot_phi[-1])]])
            new_node = np.einsum('ij,jn->in', rot_matrix, temp_node_last.T).T
            # 处理重复顶点
            trans_matrix[0] = trans_matrix[4]
            trans_matrix[1] = trans_matrix[5]
            trans_matrix[2] = trans_matrix[6]
            trans_matrix[3] = trans_matrix[7]
            trans_matrix[4] = origin_trans_matrix[0]
            trans_matrix[5] = origin_trans_matrix[1]
            trans_matrix[6] = origin_trans_matrix[2]
            trans_matrix[7] = origin_trans_matrix[3]
            # 处理重复边上节点
            trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)] \
                = trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)]
            trans_matrix[len(key_points) + (n1 + n2 + n3 - 3):len(key_points) + 2 * (n1 + n2 + n3 - 3)] \
                = origin_trans_matrix[len(key_points):len(key_points) + (n1 + n2 + n3 - 3)]

            # 其他节点
            trans_matrix[8:len(key_points)] += single_node_num - 4
            trans_matrix[len(key_points) + 2 * (n1 + n2 + n3 - 3):] += single_node_num - (n1 + n2 + n3 + 1)

            new_cell = trans_matrix[origin_cell]
            tooth_node = np.concatenate([tooth_node, new_node], axis=0)
            tooth_cell = np.concatenate([tooth_cell, new_cell], axis=0)

            t_mesh = QuadrangleMesh(tooth_node, tooth_cell)

            self.mesh = t_mesh
            return t_mesh


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import json

    # 外齿轮
    # ================================================
    # 参数读取
    # with open('./external_gear_data.json', 'r') as file:
    #     data = json.load(file)
    # m_n = data['mn']  # 法向模数
    # z = data['z']  # 齿数
    # alpha_n = data['alpha_n']  # 法向压力角
    # beta = data['beta']  # 螺旋角
    # x_n = data['xn']  # 法向变位系数
    # hac = data['hac']  # 齿顶高系数
    # cc = data['cc']  # 顶隙系数
    # rcc = data['rcc']  # 刀尖圆弧半径
    # jn = data['jn']  # 法向侧隙
    # n1 = data['n1']  # 渐开线分段数
    # n2 = data['n2']  # 过渡曲线分段数
    # n3 = data['n3']
    # na = data['na']
    # nf = data['nf']
    # inner_diam = data['inner_diam']  # 轮缘内径
    # chamfer_dia = data['chamfer_dia']  # 倒角高度（直径）
    #
    # external_gear = ExternalGear(m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf, chamfer_dia,
    #                              inner_diam)
    # quad_mesh = external_gear.generate_mesh()
    # external_gear.show_mesh()
    # ==================================================
    # 内齿轮
    # ==================================================
    # 参数读取
    with open('./internal_gear_data.json', 'r') as file:
        data = json.load(file)
    m_n = data['mn']  # 法向模数
    z = data['z']  # 齿数
    alpha_n = data['alpha_n']  # 法向压力角
    beta = data['beta']  # 螺旋角
    x_n = data['xn']  # 法向变位系数
    hac = data['hac']  # 齿顶高系数
    cc = data['cc']  # 顶隙系数
    rcc = data['rcc']  # 刀尖圆弧半径
    jn = data['jn']  # 法向侧隙
    n1 = data['n1']  # 渐开线分段数
    n2 = data['n2']  # 过渡曲线分段数
    n3 = data['n3']
    na = data['na']
    nf = data['nf']
    outer_diam = data['outer_diam']  # 轮缘内径
    z_cutter = data['z_cutter']
    xn_cutter = data['xn_cutter']

    internal_gear = InternalGear(m_n, z, alpha_n, beta, x_n, hac, cc, rcc, jn, n1, n2, n3, na, nf, outer_diam, z_cutter, xn_cutter)
    q_mesh = internal_gear.generate_mesh()
    internal_gear.show_mesh()