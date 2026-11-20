# Data provenance

**Retrieved:** 2026-11-20 01:36 UTC

**Source:** Allen Institute for Brain Science, Allen Cell Types Database.

**API endpoints:**

- Metadata: `https://api.brain-map.org/api/v2/data/query.json?criteria=model::ApiCellTypesSpecimenDetail,rma::criteria,[donor__species$il'mus musculus'],rma::options[num_rows$eqall]`
- Electrophysiology: `https://api.brain-map.org/api/v2/data/query.json?criteria=model::EphysFeature,rma::criteria,specimen(ephys_result[failed$eqfalse]),rma::options[num_rows$eqall]`

**Rows retrieved:** 1,920 mouse metadata rows; 2,333 electrophysiology feature rows.

**Primary analysis cohort:** 1,813 mouse cells with a matching electrophysiology record and a `spiny` or `aspiny` dendrite label.

**Class counts:** {'aspiny': 921, 'spiny': 892}

**Files:**

- `raw/allen_mouse_cell_metadata.csv`: source metadata table.
- `raw/allen_ephys_features_all_species.csv`: source electrophysiology feature table; filter to mouse during the metadata merge.
- `allen_mouse_spiny_aspiny_analysis.csv`: merged primary cohort before feature selection and missing-value handling.

**Documentation:** https://brain-map.org/support/documentation/cell-types-database-api
