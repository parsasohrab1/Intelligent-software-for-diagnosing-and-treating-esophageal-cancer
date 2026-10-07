"""
Catalog of real-world esophageal-cancer data resources.

Each entry states HOW MUCH we actually verified. ``verification``:
  * ``live``       - the endpoint was queried and the numbers confirmed on 2026-10-07
  * ``literature`` - taken from papers / documentation found by search; NOT confirmed live
Facts under ``literature`` must be re-checked before relying on them (counts, licences, hosts).

``integration`` describes what the product does with the resource today:
  * ``validated``       - connector implemented AND used in the pre-registered validation
  * ``verified_only``   - reachable/described, but no connector (and not used in validation)
  * ``not_integrated``  - needs a data-use agreement, a download pipeline, or is non-commercial
"""
from typing import Dict, List

CATALOG_VERIFIED_ON = "2026-10-07"

CATALOG: List[Dict] = [
    # ----- integrated + used in validation (verified live) ---------------------------
    {
        "id": "tcga-esca-gdc",
        "name": "TCGA-ESCA clinical (NCI GDC)",
        "modality": "clinical + outcomes (+ multi-omics, pathology slides available)",
        "disease": "Esophageal carcinoma (ESCC + EAC)",
        "size": "185 cases, 11,170 files (GDC Data Release 46.0)",
        "access": "open (clinical); controlled for raw sequencing",
        "license_or_terms": "GDC data access policy / TCGA data use certification",
        "url": "https://portal.gdc.cancer.gov/projects/TCGA-ESCA",
        "verification": "live",
        "integration": "validated",
        "connector": "app.services.real_data.sources.fetch_tcga_esca",
        "notes": "Staging mixes AJCC editions; median follow-up is short (18 months).",
    },
    {
        "id": "gse53624",
        "name": "GSE53624 - lncRNA profile and survival in ESCC",
        "modality": "microarray expression + clinical (TNM, survival)",
        "disease": "ESCC (China)",
        "size": "119 patients (tumour + matched normal = 238 samples)",
        "access": "open",
        "license_or_terms": "NCBI GEO terms",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE53624",
        "verification": "live",
        "integration": "validated",
        "connector": "app.services.real_data.sources.fetch_gse53624",
        "notes": "Only the clinical header is downloaded; expression matrix (69 MB) not used yet.",
    },
    {
        "id": "icgc-escc-cbioportal",
        "name": "ESCC (ICGC, Nature 2014) via cBioPortal escc_icgc",
        "modality": "clinical + WES/WGS mutations",
        "disease": "ESCC (China)",
        "size": "88 patients",
        "access": "open",
        "license_or_terms": "cBioPortal public study terms",
        "url": "https://www.cbioportal.org/study/summary?id=escc_icgc",
        "verification": "live",
        "integration": "validated",
        "connector": "app.services.real_data.sources.fetch_icgc_escc",
        "notes": "Genomic layer available but not yet used by any model.",
    },
    # ----- reachable / described, no connector ---------------------------------------
    {
        "id": "tcia-tcga-esca-ct",
        "name": "TCGA-ESCA radiology (TCIA)",
        "modality": "CT (DICOM)",
        "disease": "Esophageal carcinoma",
        "size": "16 participants / 17 studies / ~10.9 GB (per TCIA wiki)",
        "access": "open (NBIA Data Retriever)",
        "license_or_terms": "CC BY 3.0 (per TCIA wiki)",
        "url": "https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=19039398",
        "verification": "live",  # NBIA API answered for this collection; counts/licence from TCIA wiki
        "integration": "verified_only",
        "notes": "Too small to validate an imaging model; usable for pipeline smoke tests.",
    },
    {
        "id": "cbio-esca-pancan",
        "name": "Esophageal carcinoma (TCGA PanCancer Atlas) - cBioPortal",
        "modality": "clinical + multi-omics",
        "disease": "ESCA",
        "size": "182 samples (live study summary)",
        "access": "open",
        "license_or_terms": "cBioPortal public study terms",
        "url": "https://www.cbioportal.org/study/summary?id=esca_tcga_pan_can_atlas_2018",
        "verification": "live",
        "integration": "verified_only",
        "notes": "Same patients as TCGA-ESCA - NOT an independent validation cohort.",
    },
    {
        "id": "cbio-esca-broad",
        "name": "Esophageal adenocarcinoma (DFCI, Nat Genet 2013) - cBioPortal",
        "modality": "clinical (T/N stage, Barrett's, smoking) + exome",
        "disease": "EAC",
        "size": "151 samples",
        "access": "open",
        "license_or_terms": "cBioPortal public study terms",
        "url": "https://www.cbioportal.org/study/summary?id=esca_broad",
        "verification": "live",
        "integration": "verified_only",
        "notes": "No overall-survival fields -> cannot validate a survival model; useful for EAC genomics.",
    },
    {
        "id": "cbio-escc-ucla",
        "name": "ESCC (UCLA, Nat Genet 2014) - cBioPortal",
        "modality": "clinical + exome",
        "disease": "ESCC",
        "size": "139 samples",
        "access": "open",
        "license_or_terms": "cBioPortal public study terms",
        "url": "https://www.cbioportal.org/study/summary?id=escc_ucla_2014",
        "verification": "live",
        "integration": "verified_only",
        "notes": "No survival fields.",
    },
    # ----- literature-reported (NOT verified live) ----------------------------------
    {
        "id": "gse43732-gse55856",
        "name": "GSE43732 / GSE55856 - ESCC microarray (paired tumour/normal)",
        "modality": "microarray expression",
        "disease": "ESCC",
        "size": "119 + 108 tumour/normal pairs (as reported in a prognostic-signature paper)",
        "access": "open (GEO)",
        "license_or_terms": "NCBI GEO terms",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE43732",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Candidate for a tumour-vs-normal diagnostic (expression) model; clinical fields not checked.",
    },
    {
        "id": "escc-integrated-cohort-2022",
        "name": "Integrated ESCC cohort (Nat Commun 2022)",
        "modality": "WES/WGS (SRA SRP099292, SRP033394) + mutation records (Synapse syn27304838)",
        "disease": "ESCC",
        "size": "multi-cohort (see paper)",
        "access": "SRA open; Synapse requires an account",
        "license_or_terms": "per accession",
        "url": "https://www.nature.com/articles/s41467-022-32962-1",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Synapse access needs authentication (not available in this environment).",
    },
    {
        "id": "hyperkvasir",
        "name": "HyperKvasir (GI endoscopy images and videos)",
        "modality": "endoscopy",
        "disease": "GI incl. Barrett's esophagus / esophagitis classes (not esophageal cancer)",
        "size": "110,079 images + 374 videos; 10,662 labelled images (per paper)",
        "access": "open (OSF / Simula mirror)",
        "license_or_terms": "CC BY 4.0 (per paper)",
        "url": "https://www.nature.com/articles/s41597-020-00622-y",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "The Simula host failed TLS from this environment; use the OSF copy. Labels are not cancer labels.",
    },
    {
        "id": "endovis-barrett-2015",
        "name": "MICCAI 2015 EndoVis Barrett's challenge",
        "modality": "endoscopy with expert delineations",
        "disease": "Barrett's dysplasia vs early adenocarcinoma",
        "size": "100 images from 39 individuals (per paper)",
        "access": "challenge site (grand-challenge)",
        "license_or_terms": "check challenge page",
        "url": "https://arxiv.org/abs/2101.07209",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Most cancer-specific public endoscopy set found, but very small.",
    },
    {
        "id": "rare25",
        "name": "RARE25 challenge (Barrett's neoplasia detection)",
        "modality": "endoscopy",
        "disease": "Barrett's neoplasia",
        "size": "3,095 training images (158 neoplasia) per paper",
        "access": "challenge site",
        "license_or_terms": "CC BY-NC-SA (NON-COMMERCIAL) per paper",
        "url": "https://arxiv.org/abs/2604.11171",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Non-commercial licence: cannot be used to train a commercial product without separate permission.",
    },
    {
        "id": "segthor",
        "name": "SegTHOR (thoracic organ-at-risk CT incl. esophagus)",
        "modality": "CT segmentation",
        "disease": "organ segmentation (not tumour)",
        "size": "see challenge",
        "access": "challenge site",
        "license_or_terms": "check challenge page",
        "url": "https://competitions.codalab.org/competitions/21145",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Esophagus organ labels, not tumour labels.",
    },
    {
        "id": "seer",
        "name": "SEER (NCI registry)",
        "modality": "population registry (stage, treatment, survival)",
        "disease": "all esophageal cancers",
        "size": "very large (registry)",
        "access": "free but requires a signed data-use agreement (SEER*Stat)",
        "license_or_terms": "SEER Research Data Agreement",
        "url": "https://seer.cancer.gov/data/",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Best public source for treatment/stage-stratified survival at scale; needs user registration.",
    },
    {
        "id": "ncdb",
        "name": "National Cancer Database (NCDB)",
        "modality": "hospital registry",
        "disease": "all esophageal cancers",
        "size": "very large",
        "access": "application via a CoC-accredited programme",
        "license_or_terms": "NCDB Participant User File agreement",
        "url": "https://www.facs.org/quality-programs/cancer-programs/national-cancer-database/",
        "verification": "literature",
        "integration": "not_integrated",
        "notes": "Not obtainable without institutional application.",
    },
]


def catalog_summary() -> Dict:
    by_integration: Dict[str, int] = {}
    for entry in CATALOG:
        by_integration[entry["integration"]] = by_integration.get(entry["integration"], 0) + 1
    return {
        "verified_on": CATALOG_VERIFIED_ON,
        "total": len(CATALOG),
        "by_integration": by_integration,
        "live_verified": sum(1 for e in CATALOG if e["verification"] == "live"),
    }
