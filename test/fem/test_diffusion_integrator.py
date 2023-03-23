import numpy as np
import pytest
from fealpy.decorator import cartesian
from fealpy.mesh import TriangleMesh
from fealpy.functionspace import LagrangeFiniteElementSpace
from fealpy.fem import DiffusionIntegrator 

@pytest.mark.parametrize('p', [1, 2, 3, 4, 5, 6])
def test_one_equ_triangle_mesh(p):
    mesh = TriangleMesh.from_one_triangle(meshtype='equ')
    space = LagrangeFiniteElementSpace(mesh, p=p)
    di = DiffusionIntegrator(q=p+3)
    M = di.assembly_cell_matrix(space, space)
    cell2dof = space.cell_to_dof()
    M0 = space.stiff_matrix().toarray()
    M0 = M0[cell2dof[0], :][:, cell2dof[0]]
    assert np.allclose(M[0], M0)

@pytest.mark.parametrize('p', [1, 2, 3, 4, 5, 6])
def test_one_iso_triangle_mesh(p):
    mesh = TriangleMesh.from_one_triangle(meshtype='iso')
    space = LagrangeFiniteElementSpace(mesh, p=p)
    di = DiffusionIntegrator(q=p+3)
    M = di.assembly_cell_matrix(space, space)
    cell2dof = space.cell_to_dof()
    M0 = space.stiff_matrix().toarray()
    M0 = M0[cell2dof[0], :][:, cell2dof[0]]
    assert np.allclose(M[0], M0)


@pytest.mark.parametrize('p', [1, 2, 3, 4, 5, 6])
def test_one_equ_triangle_mesh_with_scalar_coef(p):
    @cartesian
    def coef(p):
        x = p[..., 0]
        return x**2 + 1
    mesh = TriangleMesh.from_one_triangle(meshtype='equ')
    space = LagrangeFiniteElementSpace(mesh, p=p)
    di = DiffusionIntegrator(coef, q=p+3)
    M = di.assembly_cell_matrix(space, space)
    cell2dof = space.cell_to_dof()
    M0 = space.stiff_matrix(c=coef).toarray()
    M0 = M0[cell2dof[0], :][:, cell2dof[0]]
    assert np.allclose(M[0], M0)

@pytest.mark.parametrize('p', [1, 2, 3, 4, 5, 6])
def test_one_equ_triangle_mesh_with_matrix_coef(p):
    @cartesian
    def coef(p):
        x = p[..., 0]
        y = p[..., 1]
        val = np.zeros(p.shape[:-1] + (2, 2), np.float64)
        val[..., 0, 0] = x**2+1
        val[..., 1, 1] = y**2+1
        return val 
    mesh = TriangleMesh.from_one_triangle(meshtype='equ')
    space = LagrangeFiniteElementSpace(mesh, p=p)
    di = DiffusionIntegrator(coef, q=p+3)
    M = di.assembly_cell_matrix(space, space)
    cell2dof = space.cell_to_dof()
    M0 = space.stiff_matrix(c=coef).toarray()
    M0 = M0[cell2dof[0], :][:, cell2dof[0]]
    assert np.allclose(M[0], M0)
