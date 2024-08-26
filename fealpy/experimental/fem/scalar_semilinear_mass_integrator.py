from typing import Optional

from ..backend import backend_manager as bm
from ..typing import TensorLike, Index, _S

from ..mesh import HomogeneousMesh
from ..functionspace.space import FunctionSpace as _FS
from ..utils import process_coef_func
from ..functional import bilinear_integral, linear_integral, get_semilinear_coef
from .integrator import (
    SemilinearInt, OpInt, CellInt,
    enable_cache,
    assemblymethod,
    CoefLike
)


class ScalarSemilinearMassIntegrator(SemilinearInt, OpInt, CellInt):
    def __init__(self, coef: Optional[CoefLike]=None, q: int=3, *,
                 index: Index=_S,
                 batched: bool=False,
                 method: Optional[str]=None) -> None:
        method = 'assembly' if (method is None) else method
        super().__init__(method=method)
        self.coef = coef
        if hasattr(coef, 'uh'):
            self.uh = coef.uh
            self.func = coef.kernel_func
            if bm.backend_name in {'jax', 'torch'}:
                pass
            else:
                self.grad_func = coef.grad_kernel_func
        self.q = q
        self.index = index
        self.batched = batched

    @enable_cache
    def to_global_dof(self, space: _FS) -> TensorLike:
        return space.cell_to_dof()[self.index]

    @enable_cache
    def fetch(self, space: _FS):
        q = self.q
        index = self.index
        mesh = getattr(space, 'mesh', None)

        if not isinstance(mesh, HomogeneousMesh):
            raise RuntimeError("The ScalarMassIntegrator only support spaces on"
                               f"homogeneous meshes, but {type(mesh).__name__} is"
                               "not a subclass of HomoMesh.")

        cm = mesh.entity_measure('cell', index=index)
        qf = mesh.quadrature_formula(q, 'cell')
        bcs, ws = qf.get_quadrature_points_and_weights()
        phi = space.basis(bcs, index=index)
        return bcs, ws, phi, cm, index
    
    def assembly(self, space: _FS) -> TensorLike:
        uh = self.uh
        coef = self.coef
        mesh = getattr(space, 'mesh', None)
        bcs, ws, phi, cm, index = self.fetch(space)
        val_A = coef.grad_kernel_func(uh(bcs))  #(C, Q)
        val_F = -coef.kernel_func(uh(bcs))      #(C, Q)
        coef = process_coef_func(coef, bcs=bcs, mesh=mesh, etype='cell', index=index)
        coef_A = get_semilinear_coef(val_A, coef)
        coef_F = get_semilinear_coef(val_F, coef)

        return bilinear_integral(phi, phi, ws, cm, coef_A, batched=self.batched), \
               linear_integral(phi, ws, cm, coef_F, batched=self.batched)