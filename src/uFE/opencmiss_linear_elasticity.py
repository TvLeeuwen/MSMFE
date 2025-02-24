#!/usr/bin/env python
"""
Calculate linear elasticity displacement, stress, strain, and elastic work for mmg
based adapted tetrahedral meshes using OpenCMISS by calling `calculate_linear_elasticity()`
Adapted from Chris Bradley
By Timo van Leeuwen
"""
# Imports ---------------------------------------------------------------------
import os

try:
    print(f"-- Conda environment detected: {os.environ['CONDA_DEFAULT_ENV']}")
except KeyError:
    print("-- Warning: No conda environment detected")

try:
    import sys
    import meshio
    import argparse
    import numpy as np
    import pandas as pd

    sys.path.append(
        r"~/OpenCMISS/install/x86_64_linux/intel-C2021.10-intel-F2021.10/ \
    intel_system/lib/python3.10/Release/opencmiss.iron"
    )
    # from opencmiss.iron import iron
except ModuleNotFoundError as e:
    sys.exit(f"-- {e}")


# Defs ------------------------------------------------------------------------


def parse_arguments():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate an initial mesh for mmg based mesh adaptation",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Use switches followed by '=' to use CLI file autocomplete, \
        example '-i='",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input path to .mesh file",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename .vtk",
        default=None,
    )
    parser.add_argument(
        "-d",
        "--dirichlet",
        type=str,
        help="Path to Dirichlet boundary nodes file (.npy) ",
        default=None,
    )
    parser.add_argument(
        "-n",
        "--neumann",
        type=str,
        help="Path to Neumann boundary nodes file (.npy) ",
        default=None,
    )
    parser.add_argument(
        "-dd",
        "--design",
        type=str,
        help="Path to design element nodes file (.npy) ",
        default=None,
    )
    return parser.parse_args()


# Main ------------------------------------------------------------------------
def calculate_linear_elasticity(
    input_path,
    output_path=None,
    dirichlet_path=None,
    neumann_path=None,
    design_path=None,
) -> None:
    """
    Calculate linear elasticity using OpenCMISS
    :param `input_path`: /Path/to/input/mesh`.mesh`
    :(optional) param: `output_path`: /Path/to/output/mesh`.vtk`
    :(optional) param: `neumann_path`: /Path/to/neumann/bc/file`.npy`
    :(optional) param: `dirichlet_path`: /Path/to/dirichlet/bc/file`.npy`
    @returns: void
    @outputs:
    :path `output_file`.vtk: solution file for visualisation and analysis
    :path `output_file`_displaced.vtk: solution file with displaced mesh
    """
    # -----------------------------------------------------------------------------------------------------------
    # IMPORT EXTERNAL MESH
    # -----------------------------------------------------------------------------------------------------------

    # Set up defaults paths
    if output_path is None:
        output_path = os.path.splitext(input_file)[0] + "_solution.vtk"
    if dirichlet_path is None:
        dirichlet_path = os.path.splitext(input_file)[0] + "_dirichlet_BC.npy"
    if neumann_path is None:
        neumann_path = os.path.splitext(input_file)[0] + "_neumann_BC.npy"

    # Import mesh data
    mesh = meshio.read(input_path)

    coords = mesh.points
    nodes = range(1, len(coords) + 1)

    eNodes = mesh.cells_dict["tetra"] + 1
    elems = range(1, len(mesh.cells_dict["tetra"]) + 1)
    triangles = len(mesh.cells_dict["triangle"])
    lines = len(mesh.cells_dict["line"])

    print(
        f"-- Mesh loaded: Vertices: {len(coords)}, Tetrahedra: {len(elems)}.\n"
        f" - Triangles: {triangles}, Lines: {lines}, Total: {len(elems) + triangles + lines}"
    )

    # Import boundary node data
    try:
        df = pd.read_json(dirichlet_path, orient="records", lines=True)
        dirichletNodes = df["dirichlet_nodes"] + 1

        df = pd.read_json(neumann_path, orient="records", lines=True)
        neumannNodes = df["dirichlet_nodes"] + 1

        df = pd.read_json(design_path, orient="records", lines=True)
        designNodes = df["dirichlet_nodes"] + 1

    except Exception as e:
        print(e)
    else:
        print(
            f"-- Boundary nodes loaded:\n - "
                f"Dirichlet: {len(dirichletNodes)}, Neumann: {len(neumannNodes)}"
        )
        print(designNodes)

    sys.exit()

    # -----------------------------------------------------------------------------------------------------------
    # SET PROBLEM PARAMETERS
    # -----------------------------------------------------------------------------------------------------------

    YOUNGS_MODULUS = 30.0e6  # mg.mm^-1.ms^-2
    POISSONS_RATIO = 0.3
    THICKNESS = 1.0  # mm (for plane strain and stress)

    LINEAR_LAGRANGE = 1
    QUADRATIC_LAGRANGE = 2
    CUBIC_LAGRANGE = 3
    CUBIC_HERMITE = 4
    LINEAR_SIMPLEX = 5
    QUADRATIC_SIMPLEX = 6
    CUBIC_SIMPLEX = 7

    DIRICHLET_BCS = 1
    NEUMANN_BCS = 2

    # Boundary condition for 1 & 2D. Analytic for 3D
    DOWNWARD_FORCE = 10.0  # N.mm^-2
    # Scale displacement for visualisation purposes
    SCALE_DISPLACEMENT = 1e3
    DIRICHLET_VECTOR = -5
    print(
        f"-- Neumann nodes downward force set: {DOWNWARD_FORCE} N, \
        displacement scaled: {SCALE_DISPLACEMENT}"
    )

    (
        CONTEXT_USER_NUMBER,
        COORDINATE_SYSTEM_USER_NUMBER,
        REGION_USER_NUMBER,
        BASIS_USER_NUMBER,
        GENERATED_MESH_USER_NUMBER,
        MESH_USER_NUMBER,
        DECOMPOSITION_USER_NUMBER,
        DECOMPOSER_USER_NUMBER,
        GEOMETRIC_FIELD_USER_NUMBER,
        ELASTICITY_DEPENDENT_FIELD_USER_NUMBER,
        ELASTICITY_MATERIALS_FIELD_USER_NUMBER,
        ELASTICITY_ANALYTIC_FIELD_USER_NUMBER,
        ELASTICITY_DERIVED_FIELD_USER_NUMBER,
        ELASTICITY_EQUATIONS_SET_FIELD_USER_NUMBER,
        ELASTICITY_EQUATIONS_SET_USER_NUMBER,
        ELASTICITY_PROBLEM_USER_NUMBER,
    ) = range(1, 17)

    NUMBER_OF_GAUSS_XI = 4

    interpolationType = LINEAR_SIMPLEX
    numberOfDimensions = 3

    interpolationTypeXi = iron.BasisInterpolationSpecifications.LINEAR_SIMPLEX
    numberOfNodesXi = 2
    gaussOrder = 4

    haveHermite = interpolationType == CUBIC_HERMITE
    haveSimplex = (
        interpolationType == LINEAR_SIMPLEX
        or interpolationType == QUADRATIC_SIMPLEX
        or interpolationType == CUBIC_SIMPLEX
    )

    numberOfXi = numberOfDimensions

    # -------------------------------------------- N/mm2---------------------------------------------------------------
    # CONTEXT AND WORLD REGION
    # -----------------------------------------------------------------------------------------------------------
    print("-- Setting up model")

    context = iron.Context()
    context.Create(CONTEXT_USER_NUMBER)

    worldRegion = iron.Region()
    context.WorldRegionGet(worldRegion)

    # -----------------------------------------------------------------------------------------------------------
    # DIAGNOSTICS AND COMPUTATIONAL NODE INFORMATION
    # -----------------------------------------------------------------------------------------------------------

    # iron.OutputSetOn("LinearCantilever")

    # iron.DiagnosticsSetOn(iron.DiagnosticTypes.IN,[1,2,3,4,5],"",["BoundaryConditionsVariable_NeumannIntegrate"])

    # Get the computational nodes information
    computationEnvironment = iron.ComputationEnvironment()
    context.ComputationEnvironmentGet(computationEnvironment)
    numberOfComputationalNodes = computationEnvironment.NumberOfWorldNodesGet()
    computationalNodeNumber = computationEnvironment.WorldNodeNumberGet()

    worldWorkGroup = iron.WorkGroup()
    computationEnvironment.WorldWorkGroupGet(worldWorkGroup)

    # -----------------------------------------------------------------------------------------------------------
    # COORDINATE SYSTEM
    # -----------------------------------------------------------------------------------------------------------

    coordinateSystem = iron.CoordinateSystem()
    coordinateSystem.CreateStart(COORDINATE_SYSTEM_USER_NUMBER, context)
    coordinateSystem.DimensionSet(numberOfDimensions)
    coordinateSystem.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # REGION
    # -----------------------------------------------------------------------------------------------------------

    region = iron.Region()
    region.CreateStart(REGION_USER_NUMBER, worldRegion)
    region.LabelSet("Cantilever")
    region.CoordinateSystemSet(coordinateSystem)
    region.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # BASIS
    # -----------------------------------------------------------------------------------------------------------
    print(" - Setting basis")

    basis = iron.Basis()

    basis.CreateStart(BASIS_USER_NUMBER, context)
    basis.TypeSet(iron.BasisTypes.SIMPLEX)
    basis.NumberOfXiSet(numberOfXi)
    basis.InterpolationXiSet([interpolationTypeXi] * numberOfXi)
    basis.QuadratureOrderSet(gaussOrder)

    basis.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # MESH
    # -----------------------------------------------------------------------------------------------------------
    print(" - Building mesh")

    ocnodes = iron.Nodes()
    ocnodes.CreateStart(region, len(nodes) + 1)
    ocnodes.CreateFinish()
    mesh = iron.Mesh()
    mesh.CreateStart(1, region, 3)
    mesh.NumberOfElementsSet(len(elems) + 1)
    mesh.NumberOfComponentsSet(1)
    meshElements = iron.MeshElements()

    meshElements.CreateStart(mesh, 1, basis)

    for element in elems:
        # elem = element.item()
        localNodes = np.array(eNodes[element - 1], dtype=np.int32)
        meshElements.NodesSet(element, localNodes)
    meshElements.CreateFinish()
    mesh.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # MESH DECOMPOSITION
    # -----------------------------------------------------------------------------------------------------------
    print(" - Mesh decompition")

    decomposition = iron.Decomposition()
    decomposition.CreateStart(DECOMPOSITION_USER_NUMBER, mesh)
    decomposition.TypeSet(iron.DecompositionTypes.CALCULATED)
    decomposition.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # DECOMPOSER
    # -----------------------------------------------------------------------------------------------------------

    decomposer = iron.Decomposer()
    decomposer.CreateStart(DECOMPOSER_USER_NUMBER, worldRegion, worldWorkGroup)
    decompositionIndex = decomposer.DecompositionAdd(decomposition)
    decomposer.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # GEOMETRIC FIELD
    # -----------------------------------------------------------------------------------------------------------
    print(" - Setting up geometric field")

    geometricField = iron.Field()
    geometricField.CreateStart(GEOMETRIC_FIELD_USER_NUMBER, region)
    geometricField.DecompositionSet(decomposition)
    geometricField.TypeSet(iron.FieldTypes.GEOMETRIC)
    geometricField.VariableLabelSet(iron.FieldVariableTypes.U, "Geometry")
    geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U, 1, 1)
    geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U, 2, 1)
    if numberOfDimensions == 3:
        geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U, 3, 1)
    geometricField.CreateFinish()

    # Set geometry
    for node in range(1, len(nodes) + 1):
        x = coords[node - 1, 0].item()
        y = coords[node - 1, 1].item()
        z = coords[node - 1, 2].item()
        geometricField.ParameterSetUpdateNode(
            iron.FieldVariableTypes.U,
            iron.FieldParameterSetTypes.VALUES,
            1,
            1,
            node,
            1,
            x,
        )
        geometricField.ParameterSetUpdateNode(
            iron.FieldVariableTypes.U,
            iron.FieldParameterSetTypes.VALUES,
            1,
            1,
            node,
            2,
            y,
        )
        geometricField.ParameterSetUpdateNode(
            iron.FieldVariableTypes.U,
            iron.FieldParameterSetTypes.VALUES,
            1,
            1,
            node,
            3,
            z,
        )

    # -----------------------------------------------------------------------------------------------------------
    # EQUATION SETS
    # -----------------------------------------------------------------------------------------------------------
    print(" - Setting equation sets")

    # Create linear elasiticity equations set
    elasticityEquationsSetField = iron.Field()
    elasticityEquationsSet = iron.EquationsSet()

    elasticityEquationsSetSpecification = [
        iron.EquationsSetClasses.ELASTICITY,
        iron.EquationsSetTypes.LINEAR_ELASTICITY,
        iron.EquationsSetSubtypes.THREE_DIMENSIONAL_ISOTROPIC,
    ]

    elasticityEquationsSet.CreateStart(
        ELASTICITY_EQUATIONS_SET_USER_NUMBER,
        region,
        geometricField,
        elasticityEquationsSetSpecification,
        ELASTICITY_EQUATIONS_SET_FIELD_USER_NUMBER,
        elasticityEquationsSetField,
    )
    elasticityEquationsSet.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # EQUATIONS SET DEPENDENT
    # -----------------------------------------------------------------------------------------------------------
    print("     - Dependent field")

    # elasticityDependentField = iron.Field()
    # elasticityEquationsSet.DependentCreateStart(ELASTICITY_DEPENDENT_FIELD_USER_NUMBER,elasticityDependentField)
    # elasticityDependentField.TypeSet(iron.FieldTypes.GENERAL)
    # elasticityDependentField.MeshDecompositionSet(decomposition)
    # elasticityDependentField.GeometricFieldSet(geometricField)
    # elasticityDependentField.DependentTypeSet(iron.Field.DependentTypes.DEPENDENT)
    # elasticityDependentField.LabelSet("ElasticityDependent")
    # elasticityDependentField.NumberOfVariablesSet(2)
    # elasticityDependentField.VariableLabelSet(iron.FieldVariableTypes.U,"Displacement")
    # elasticityDependentField.VariableLabelSet(iron.FieldVariableTypes.DELUDELN,"Traction")
    # elasticityDependentField.NumberOfComponentsSet(iron.FieldVariableTypes.U,3)
    # elasticityDependentField.NumberOfComponentsSet(iron.FieldVariableTypes.DELUDELN,3)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,1)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,1)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,1)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.DELUDELN,1,1)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.DELUDELN,2,1)
    # elasticityDependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.DELUDELN,3,1)
    # elasticityEquationsSet.DependentCreateFinish()

    elasticityDependentField = iron.Field()
    elasticityEquationsSet.DependentCreateStart(
        ELASTICITY_DEPENDENT_FIELD_USER_NUMBER, elasticityDependentField
    )
    elasticityDependentField.LabelSet("ElasticityDependent")
    elasticityDependentField.VariableLabelSet(iron.FieldVariableTypes.U, "Displacement")
    elasticityDependentField.VariableLabelSet(iron.FieldVariableTypes.T, "Traction")
    elasticityEquationsSet.DependentCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # EQUATIONS SET MATERIALS
    # -----------------------------------------------------------------------------------------------------------
    print("     - Materials field")

    elasticityMaterialsField = iron.Field()
    elasticityEquationsSet.MaterialsCreateStart(
        ELASTICITY_MATERIALS_FIELD_USER_NUMBER, elasticityMaterialsField
    )
    elasticityMaterialsField.LabelSet("ElasticityMaterials")
    elasticityMaterialsField.VariableLabelSet(iron.FieldVariableTypes.U, "Materials")
    elasticityEquationsSet.MaterialsCreateFinish()
    # Initialise the analytic field values
    elasticityMaterialsField.ComponentValuesInitialise(
        iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, YOUNGS_MODULUS
    )
    elasticityMaterialsField.ComponentValuesInitialise(
        iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 2, POISSONS_RATIO
    )
    if numberOfDimensions == 2:
        elasticityMaterialsField.ComponentValuesInitialise(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 3, THICKNESS
        )

    # -----------------------------------------------------------------------------------------------------------
    # EQUATIONS SET ANALYTIC
    # -----------------------------------------------------------------------------------------------------------
    # print("analytic")
    # elasticityAnalyticField = iron.Field()
    # if(numberOfDimensions==3):
    #     elasticityEquationsSet.AnalyticCreateStart(iron.EquationsSetLinearElasticityAnalyticFunctionTypes.CANTILEVER_END_LOAD,
    #                                                ELASTICITY_ANALYTIC_FIELD_USER_NUMBER,elasticityAnalyticField)
    #     elasticityAnalyticField.LabelSet("ElasticityAnalytic")
    #     elasticityAnalyticField.VariableLabelSet(iron.FieldVariableTypes.U,"Analytic")
    #     elasticityEquationsSet.AnalyticCreateFinish()
    #     # Initialise the analytic field values
    #     elasticityAnalyticField.ComponentValuesInitialise(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
    #                                                       1,LENGTH)
    #     elasticityAnalyticField.ComponentValuesInitialise(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
    #                                                       2,HEIGHT)
    #     elasticityAnalyticField.ComponentValuesInitialise(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
    #                                                       3,WIDTH)
    #     elasticityAnalyticField.ComponentValuesInitialise(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
    #                                                       4,YOUNGS_MODULUS)
    #     elasticityAnalyticField.ComponentValuesInitialise(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
    #                                                       5,MAX_FORCE)

    # -----------------------------------------------------------------------------------------------------------
    # EQUATIONS SET DERIVED
    # -----------------------------------------------------------------------------------------------------------
    print("     - Derived field")
    # Create a field for the derived field. Have three variables U - Small strain tensor, V - Cauchy stress, W - Elastic Work
    if numberOfDimensions == 2:
        numberOfTensorComponents = 3
    else:
        numberOfTensorComponents = 6
    elasticityDerivedField = iron.Field()
    elasticityDerivedField.CreateStart(ELASTICITY_DERIVED_FIELD_USER_NUMBER, region)
    elasticityDerivedField.LabelSet("ElasticityDerived")
    elasticityDerivedField.TypeSet(iron.FieldTypes.GENERAL)
    elasticityDerivedField.DecompositionSet(decomposition)
    elasticityDerivedField.GeometricFieldSet(geometricField)
    elasticityDerivedField.DependentTypeSet(iron.FieldDependentTypes.DEPENDENT)
    elasticityDerivedField.NumberOfVariablesSet(3)
    elasticityDerivedField.VariableTypesSet(
        [
            iron.FieldVariableTypes.U,
            iron.FieldVariableTypes.V,
            iron.FieldVariableTypes.W,
        ]
    )
    elasticityDerivedField.VariableLabelSet(iron.FieldVariableTypes.U, "SmallStrain")
    elasticityDerivedField.VariableLabelSet(iron.FieldVariableTypes.V, "CauchyStress")
    elasticityDerivedField.VariableLabelSet(iron.FieldVariableTypes.W, "ElasticWork")
    elasticityDerivedField.NumberOfComponentsSet(
        iron.FieldVariableTypes.U, numberOfTensorComponents
    )
    elasticityDerivedField.NumberOfComponentsSet(
        iron.FieldVariableTypes.V, numberOfTensorComponents
    )
    elasticityDerivedField.NumberOfComponentsSet(iron.FieldVariableTypes.W, 1)
    for componentIdx in range(1, numberOfTensorComponents + 1):
        elasticityDerivedField.ComponentMeshComponentSet(
            iron.FieldVariableTypes.U, componentIdx, 1
        )
        elasticityDerivedField.ComponentMeshComponentSet(
            iron.FieldVariableTypes.V, componentIdx, 1
        )
    elasticityDerivedField.ComponentMeshComponentSet(iron.FieldVariableTypes.W, 1, 1)
    for componentIdx in range(1, numberOfTensorComponents + 1):
        elasticityDerivedField.ComponentInterpolationSet(
            iron.FieldVariableTypes.U,
            componentIdx,
            iron.FieldInterpolationTypes.ELEMENT_BASED,
        )
        elasticityDerivedField.ComponentInterpolationSet(
            iron.FieldVariableTypes.V,
            componentIdx,
            iron.FieldInterpolationTypes.ELEMENT_BASED,
        )
    elasticityDerivedField.ComponentInterpolationSet(
        iron.FieldVariableTypes.W, 1, iron.FieldInterpolationTypes.ELEMENT_BASED
    )
    elasticityDerivedField.CreateFinish()

    # Create the derived equations set fields
    elasticityEquationsSet.DerivedCreateStart(
        ELASTICITY_DERIVED_FIELD_USER_NUMBER, elasticityDerivedField
    )
    elasticityEquationsSet.DerivedVariableSet(
        iron.EquationsSetDerivedTensorTypes.SMALL_STRAIN, iron.FieldVariableTypes.U
    )
    elasticityEquationsSet.DerivedVariableSet(
        iron.EquationsSetDerivedTensorTypes.CAUCHY_STRESS, iron.FieldVariableTypes.V
    )
    elasticityEquationsSet.DerivedVariableSet(
        iron.EquationsSetDerivedTensorTypes.ELASTIC_WORK, iron.FieldVariableTypes.W
    )
    elasticityEquationsSet.DerivedCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # EQUATIONS
    # -----------------------------------------------------------------------------------------------------------
    print(" - Setting equations")

    elasticityEquations = iron.Equations()
    elasticityEquationsSet.EquationsCreateStart(elasticityEquations)
    # elasticityEquations.SparsityTypeSet(iron.EquationsSparsityTypes.FULL)
    elasticityEquations.SparsityTypeSet(iron.EquationsSparsityTypes.SPARSE)
    # elasticityEquations.OutputTypeSet(iron.EquationsOutputTypes.NONE)
    # elasticityEquations.OutputTypeSet(iron.EquationsOutputTypes.TIMING)
    # elasticityEquations.OutputTypeSet(iron.EquationsOutputTypes.MATRIX)
    elasticityEquations.OutputTypeSet(iron.EquationsOutputTypes.ELEMENT_MATRIX)
    elasticityEquationsSet.EquationsCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # PROBLEM
    # -----------------------------------------------------------------------------------------------------------
    print(" - Defining the problem")
    elasticityProblem = iron.Problem()
    elasticityProblemSpecification = [
        iron.ProblemClasses.ELASTICITY,
        iron.ProblemTypes.LINEAR_ELASTICITY,
        iron.ProblemSubtypes.NONE,
    ]
    elasticityProblem.CreateStart(
        ELASTICITY_PROBLEM_USER_NUMBER, context, elasticityProblemSpecification
    )
    elasticityProblem.CreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # CONTROL LOOPS
    # -----------------------------------------------------------------------------------------------------------

    print(" - Building control loops")
    elasticityProblem.ControlLoopCreateStart()
    elasticityProblem.ControlLoopCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # SOLVER
    # -----------------------------------------------------------------------------------------------------------
    print(" - Initiating solver")

    # Create problem solver
    elasticitySolver = iron.Solver()
    elasticityProblem.SolversCreateStart()
    elasticityProblem.SolverGet([iron.ControlLoopIdentifiers.NODE], 1, elasticitySolver)
    # elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.NONE)
    # elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.MONITOR)
    # elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.PROGRESS)
    # elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.TIMING)
    # elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.SOLVER)
    elasticitySolver.OutputTypeSet(iron.SolverOutputTypes.MATRIX)
    elasticitySolver.LinearTypeSet(iron.LinearSolverTypes.DIRECT)
    elasticityProblem.SolversCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # SOLVER EQUATIONS
    # -----------------------------------------------------------------------------------------------------------

    # Create solver equations and add equations set to solver equations
    elasticitySolver = iron.Solver()
    elasticitySolverEquations = iron.SolverEquations()
    elasticityProblem.SolverEquationsCreateStart()
    elasticityProblem.SolverGet([iron.ControlLoopIdentifiers.NODE], 1, elasticitySolver)
    elasticitySolver.SolverEquationsGet(elasticitySolverEquations)
    # elasticitySolverEquations.SparsityTypeSet(iron.SolverEquationsSparsityTypes.FULL)
    elasticitySolverEquations.SparsityTypeSet(iron.SolverEquationsSparsityTypes.SPARSE)
    elasticityEquationsSetIndex = elasticitySolverEquations.EquationsSetAdd(
        elasticityEquationsSet
    )
    elasticityProblem.SolverEquationsCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # BOUNDARY CONDITIONS
    # -----------------------------------------------------------------------------------------------------------
    print(" - Assigning boundary conditions")

    # Create analytic boundary conditions
    boundaryConditions = iron.BoundaryConditions()
    elasticitySolverEquations.BoundaryConditionsCreateStart(boundaryConditions)

    dirichletNodesBC = []
    # Set left hand edge to be built in.
    for nodeNumber in dirichletNodes:
        nodeNumber = int(nodeNumber)
        nodeDomain = decomposition.NodeDomainGet(nodeNumber, 1)
        if nodeDomain == computationalNodeNumber:
            boundaryConditions.AddNode(
                elasticityDependentField,
                iron.FieldVariableTypes.U,
                1,
                1,
                nodeNumber,
                1,
                iron.BoundaryConditionsTypes.FIXED,
                0.0,
            )
            boundaryConditions.AddNode(
                elasticityDependentField,
                iron.FieldVariableTypes.U,
                1,
                1,
                nodeNumber,
                2,
                iron.BoundaryConditionsTypes.FIXED,
                0.0,
            )
            boundaryConditions.AddNode(
                elasticityDependentField,
                iron.FieldVariableTypes.U,
                1,
                1,
                nodeNumber,
                3,
                iron.BoundaryConditionsTypes.FIXED,
                0.0,
            )
            # Show a vector in the x directions where nodes are fixed
            dirichletNodesBC.append([nodeNumber, DIRICHLET_VECTOR, 0, 0])
    dirichletNodesBC = np.array(dirichletNodesBC)

    neumannNodesBC = []
    # Set downward force on right-hand edge
    for nodeNumber in neumannNodes:
        nodeNumber = int(nodeNumber)
        nodeDomain = decomposition.NodeDomainGet(nodeNumber, 1)
        if nodeDomain == computationalNodeNumber:
            boundaryConditions.SetNode(
                elasticityDependentField,
                iron.FieldVariableTypes.T,
                1,
                1,
                nodeNumber,
                1,
                iron.BoundaryConditionsTypes.NEUMANN_POINT,
                0.0,
            )
            boundaryConditions.SetNode(
                elasticityDependentField,
                iron.FieldVariableTypes.T,
                1,
                1,
                nodeNumber,
                2,
                iron.BoundaryConditionsTypes.NEUMANN_POINT,
                DOWNWARD_FORCE,
            )
            boundaryConditions.SetNode(
                elasticityDependentField,
                iron.FieldVariableTypes.T,
                1,
                1,
                nodeNumber,
                3,
                iron.BoundaryConditionsTypes.NEUMANN_POINT,
                0.0,
            )
            neumannNodesBC.append([nodeNumber, 0, DOWNWARD_FORCE, 0])
    neumannNodesBC = np.array(neumannNodesBC)

    elasticitySolverEquations.BoundaryConditionsCreateFinish()

    # -----------------------------------------------------------------------------------------------------------
    # SOLVE
    # -----------------------------------------------------------------------------------------------------------
    print("-- Solving problem")
    elasticityProblem.Solve()

    print("-- Problem solved")

    print(" - Calculating derived fields")
    # Calculate the derived fields
    elasticityEquationsSet.DerivedVariableCalculate(
        iron.EquationsSetDerivedTensorTypes.SMALL_STRAIN
    )
    elasticityEquationsSet.DerivedVariableCalculate(
        iron.EquationsSetDerivedTensorTypes.CAUCHY_STRESS
    )
    elasticityEquationsSet.DerivedVariableCalculate(
        iron.EquationsSetDerivedTensorTypes.ELASTIC_WORK
    )

    # -----------------------------------------------------------------------------------------------------------
    # OUTPUT
    # -----------------------------------------------------------------------------------------------------------
    print("-- Output")

    ### Get nodes
    nodes = iron.MeshNodes()
    mesh.NodesGet(1, nodes)
    numberOfNodes = nodes.NumberOfNodesGet()
    numberCoords = coordinateSystem.DimensionGet()

    nodesList = [
        [0 for coord in range(0, numberCoords + 2)] for node in range(0, numberOfNodes)
    ]

    for i in range(0, numberOfNodes):
        node = i + 1
        node_coordx = geometricField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 1
        )
        node_coordy = geometricField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 2
        )
        node_coordz = geometricField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 3
        )

        node_displacement_x = elasticityDependentField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 1
        )
        node_displacement_y = elasticityDependentField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 2
        )
        node_displacement_z = elasticityDependentField.ParameterSetGetNodeDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, 1, 1, node, 3
        )
        nodesList[i] = [
            node,
            node_coordx,
            node_coordy,
            node_coordz,
            node_displacement_x,
            node_displacement_y,
            node_displacement_z,
        ]

    ### Elements
    meshElements = iron.MeshElements()
    meshNodes = iron.MeshNodes()
    mesh.ElementsGet(1, meshElements)
    mesh.NodesGet(1, meshNodes)
    elementBasis = iron.Basis()
    numberOfElements = mesh.NumberOfElementsGet()

    ### Get elements
    elementsList = [[0 for i in range(5)] for elem in range(numberOfElements)]
    for j in range(0, numberOfElements):
        elemidx = j + 1
        elemnodes = meshElements.NodesGet(elemidx, 4)
        elem_stress_sigma_11 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 1
        )
        elem_stress_sigma_22 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 2
        )
        elem_stress_sigma_33 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 3
        )
        elem_stress_sigma_23 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 4
        )
        elem_stress_sigma_13 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 5
        )
        elem_stress_sigma_12 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES, elemidx, 6
        )

        elem_strain_epsilon_11 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 1
        )
        elem_strain_epsilon_22 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 2
        )
        elem_strain_epsilon_33 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 3
        )
        elem_strain_epsilon_23 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 4
        )
        elem_strain_epsilon_13 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 5
        )
        elem_strain_epsilon_12 = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.V, iron.FieldParameterSetTypes.VALUES, elemidx, 6
        )

        elem_elastic_work = elasticityDerivedField.ParameterSetGetElementDP(
            iron.FieldVariableTypes.W, iron.FieldParameterSetTypes.VALUES, elemidx, 1
        )

        elementsList[j] = [
            elemidx,
            elemnodes[0],
            elemnodes[1],
            elemnodes[2],
            elemnodes[3],
            elem_stress_sigma_11,
            elem_stress_sigma_22,
            elem_stress_sigma_33,
            elem_stress_sigma_23,
            elem_stress_sigma_13,
            elem_stress_sigma_12,
            elem_strain_epsilon_11,
            elem_strain_epsilon_22,
            elem_strain_epsilon_33,
            elem_strain_epsilon_23,
            elem_strain_epsilon_13,
            elem_strain_epsilon_12,
            elem_elastic_work,
        ]

    nodesList = np.array(nodesList)
    elementsList = np.array(elementsList)

    ### VTK export
    # Get mesh components
    points = np.array(nodesList[:, 1:4])
    cells = [("tetra", np.array(elementsList)[:, 1:5] - 1)]
    print(f" - Fetched {numberOfNodes} nodes")
    print(f" - Fetched {numberOfElements} elements")

    # Get boundary conditions
    boundaries = np.zeros([nodesList.shape[0], 4])
    boundaries[:, 0] = nodesList[:, 0]
    for dirichlet in dirichletNodesBC:
        boundaries[dirichlet[0] - 1, 1:] = dirichlet[1:]
    for neumann in neumannNodesBC:
        boundaries[int(neumann[0] - 1), 1:] = neumann[1:]
    print(
        f" - Including boundary conditions:\n    - Downward force: {DOWNWARD_FORCE}\n    - Displacement scaled: {SCALE_DISPLACEMENT}"
    )

    # Get solutions
    displacement = nodesList[:, -3:]
    stress_11 = elementsList[:, 5]
    stress_22 = elementsList[:, 6]
    stress_33 = elementsList[:, 7]
    stress_23 = elementsList[:, 8]
    stress_13 = elementsList[:, 9]
    stress_12 = elementsList[:, -8]
    strain_11 = elementsList[:, -7]
    strain_22 = elementsList[:, -6]
    strain_33 = elementsList[:, -5]
    strain_23 = elementsList[:, -4]
    strain_13 = elementsList[:, -3]
    strain_12 = elementsList[:, -2]
    elastic_work = elementsList[:, -1]

    # Write solution mesh
    solution_mesh = meshio.Mesh(points, cells)
    solution_mesh.point_data = {
        "displacement": displacement,
        "BC": boundaries[:, 1:],
    }
    solution_mesh.cell_data = {
        "stress_11": stress_11,
        "stress_22": stress_22,
        "stress_33": stress_33,
        "stress_23": stress_23,
        "stress_13": stress_13,
        "stress_12": stress_12,
        "strain_11": strain_11,
        "strain_22": strain_22,
        "strain_33": strain_33,
        "strain_23": strain_23,
        "strain_13": strain_13,
        "strain_12": strain_12,
        "elastic_work": elastic_work,
    }
    meshio.write(output_file, solution_mesh)

    # TODO: scale displacement - make seperate module
    # Write solution with mesh displaced
    displaced_points = points + (displacement * SCALE_DISPLACEMENT)
    output_file_displaced = output_file.parents[0] / output_file.name.replace(
        ".vtk", "_displaced.vtk"
    )
    solution_mesh.points = displaced_points
    meshio.write(output_file_displaced, solution_mesh)

    print(
        f" - Exporting VTK output to {output_file.parents[0]}:\n\
    - {output_file.name}\n\
    - {output_file_displaced.name}"
    )

    # Finalise OpenCMISS
    iron.Finalise()

    print("-- Finished")


if __name__ == "__main__":
    args = parse_arguments()

    calculate_linear_elasticity(
        args.input,
        args.output,
        args.dirichlet,
        args.neumann,
        args.design,
    )
