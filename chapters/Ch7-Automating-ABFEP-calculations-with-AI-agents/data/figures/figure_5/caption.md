**Figure 5. Shared task successes coexist with scientifically consequential assembly failures.**
(A) Strict passes out of three selected replicates for all 50 tasks and five
configurations, using the harmonized manuscript results. Configurations label
rows; task IDs and concise scientific names label columns, grouped by the seven
existing task types (QM, quantum chemistry). Difficulty is shown in a separate
row: E, easy; M, medium; H, hard. The four discrete colors indicate 0, 1, 2 or 3
strict passes, rather than partial-credit scores or Pass@3. A strict pass
requires completion and full correctness and process scores. The upper strip
identifies tasks passed in all three replicates by each of Claude Opus-5.5,
GPT-6.1 Sol and GPT-6 Astra. Complete descriptions, display labels and all cell
values are retained in `task_labels_and_values.csv`. CV denotes collective
variable; COM, centre of mass; PBC, periodic boundary conditions; FF, force
field; MetaD, metadynamics; conform., conformation; altloc, alternate location.
(B) Claude Opus-5.5, Task 25, replicate 3 (`5qy4iHm`): the intermediate mGlu5–51D structure
retains ligand contact in the supplied binding pocket, whereas the submitted
assembly loses the binding pose. The two main views have matched receptor
orientation and scale after corresponding-protein alignment; the adjacent inset
enlarges the intermediate pocket. The ligand is never independently aligned.
A whole-molecule periodic image is selected for the submitted ligand, and the
dashed marker joins the actual nearest ligand–protein atom pair, ligand Cl and
Lys117 HZ2: **37.8 Å**, accounting for periodic boundaries. Correctness remained
**1.000**, while process was **0.875**; the binding-pose failure was detected by
the process assessment rather than by a final-pose correctness check.
(C) Claude Opus-5.5, Task 29, replicate 2 (`Z4DQoGB`): ligand AMP702 C6 and lipid POPE808 C316
are separated by only **1.37 Å** in the submitted PepT2 system. This is a
nonbonded ligand–lipid carbon contact; the dashed distance marker is not a
covalent bond. The corner inset enlarges the contact and includes transparent
carbon van der Waals spheres. Ligand carbons are cyan, lipid carbons muted gold,
protein cartoons pale green, and heteroatoms use conventional colors.
Correctness and process scores were **1.000** and **0.9375**, respectively.
The illustrated clash is **not established as the unique cause** of the
non-finite force reported during minimization: the log identifies a different
atom, POPG994 H4X (44170), which has a separate lipid–lipid near-overlap.
Full correctness credit therefore does not imply exhaustive structural validation.
