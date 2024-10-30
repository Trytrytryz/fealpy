"""The FEM Module"""

### Forms and bases
from .integrator import *
from .bilinear_form import BilinearForm
from .linear_form import LinearForm
from .semilinear_form import SemilinearForm
from .block_form import BlockForm
from .linear_block_form import LinearBlockForm

### Cell Operator
from .scalar_diffusion_integrator import ScalarDiffusionIntegrator
from .scalar_semilinear_diffusion_integrator import ScalarSemilinearDiffusionIntegrator
from .scalar_mass_integrator import ScalarMassIntegrator
from .scalar_semilinear_mass_integrator import ScalarSemilinearMassIntegrator
from .scalar_convection_integrator import ScalarConvectionIntegrator
from .linear_elastic_integrator import LinearElasticIntegrator
from .press_work_integrator import PressWorkIntegrator, PressWorkIntegrator0, PressWorkIntegrator1
from .vector_mass_integrator import VectorMassIntegrator
from .curl_integrator import CurlCurlIntegrator


### Cell Source
from .cell_source_integrator import CellSourceIntegrator
SourceIntegrator = CellSourceIntegrator

from .scalar_source_integrator import ScalarSourceIntegrator
from .vector_source_integrator import VectorSourceIntegrator

### Face Operator
from .scalar_robin_bc_integrator import ScalarRobinBCIntegrator
from .face_mass_integrator import BoundaryFaceMassIntegrator, InterFaceMassIntegrator

### Face Source
from .scalar_neumann_bc_integrator import ScalarNeumannBCIntegrator
from .face_source_integrator import BoundaryFaceSourceIntegrator, InterFaceSourceIntegrator

### Dirichlet BC
from .dirichlet_bc import DirichletBC
from .dirichlet_bc_operator import DirichletBCOperator

### recovery estimate
from .recovery_alg import RecoveryAlg

### Other
from .semilinear_wrapper import SemilinearWrapperInt
