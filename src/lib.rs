pub mod analysis;
pub mod gff;
pub mod results;
extern crate pyo3;

use pyo3::prelude::*;
use analysis::extractor::{BasePredictionExtractor, ComparisonExtractor};
//use analysis::hmm::show_hmm_config;
use analysis::rater::SequenceRating;
use analysis::Analyzer;
use gff::GffWriter;
use results::raw::RawHelixerPredictions;
use results::HelixerResults;
use std::fs::File;
use std::io::BufWriter;
use std::path::Path;
//use std::process::exit;



// Function that contains the logic from main.rs
pub fn helixer_post(
    genome_path: &str,
    predictions_path: &str,
    window_size: usize,
    edge_threshold: f32,
    peak_threshold: f32,
    min_coding_length: usize,
    gff_filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    // Implement your logic here using the existing modules

    let helixer_res = HelixerResults::new(predictions_path.as_ref(), genome_path.as_ref())
        .expect("Failed to open input files");

    let bp_extractor = BasePredictionExtractor::new_from_prediction(&helixer_res)
        .expect("Failed to open Base / ClassPrediction / PhasePrediction Datasets");
    //let bp_extractor = BasePredictionExtractor::new_from_pseudo_predictions(&helixer_res).expect("Failed to open Base / ClassPrediction / PhasePrediction Datasets");

    let comp_extractor = ComparisonExtractor::new(&helixer_res).expect("Failed to open ClassReference / PhaseReference / ClassPrediction / PhasePrediction Datasets");

    let analyzer = Analyzer::new(
        bp_extractor,
        comp_extractor,
        window_size,
        edge_threshold,
        peak_threshold,
        min_coding_length,
    );

    let mut total_count = 0;
    let mut total_length = 0;

    //show_hmm_config();

    let gff_file = File::create(gff_filename).unwrap();
    let mut gff_writer = GffWriter::new(BufWriter::new(gff_file));

    // There should only ever be one species for the gff output
    assert_eq!(
        helixer_res.get_all_species().len(),
        1,
        "Error: Multiple Species are not allowed for GFF output."
    );
    let rhg = RawHelixerPredictions::new(&Path::new(predictions_path))
        .expect("Error: Something went wrong while accessing the predictions.");
    let model_md5sum = rhg.get_model_md5sum().ok();
    let species_name = helixer_res.get_all_species().first().map(|x| x.get_name());

    gff_writer
        .write_global_header(species_name, model_md5sum)
        .expect(&*format!(
            "Error: Could not write header to file {}.",
            gff_filename
        ));

    for species in helixer_res.get_all_species() {
        let mut fwd_species_rating = SequenceRating::new();
        let mut rev_species_rating = SequenceRating::new();

        let id = species.get_id();
        for seq_id in helixer_res.get_sequences_for_species(id) {
            let seq = helixer_res.get_sequence_by_id(*seq_id);
            gff_writer
                .write_region_header(seq.get_name(), seq.get_length())
                .expect(&*format!(
                    "Error: Could not write sequence-region header to file {}.",
                    gff_filename
                ));

            let (count, length) = analyzer.process_sequence(
                species,
                seq,
                &mut fwd_species_rating,
                &mut rev_species_rating,
                &mut gff_writer,
            );

            total_count += count;
            total_length += length;
        }

        fwd_species_rating.dump(analyzer.has_ref());
        rev_species_rating.dump(analyzer.has_ref());

        let mut species_rating = SequenceRating::new();
        species_rating.accumulate(&fwd_species_rating);
        species_rating.accumulate(&rev_species_rating);

        species_rating.dump(analyzer.has_ref());
    }


    Ok(())
}

#[pyfunction]
fn hello_world() -> PyResult<String> {
    Ok("Hello, world!".to_string())
}

// PyO3 function to expose to Python
#[pyfunction]
fn run_helixer_post(
    genome_path: &str,
    predictions_path: &str,
    window_size: usize,
    edge_threshold: f32,
    peak_threshold: f32,
    min_coding_length: usize,
    gff_filename: &str,
) -> PyResult<()> {
    helixer_post(
        genome_path,
        predictions_path,
        window_size,
        edge_threshold,
        peak_threshold,
        min_coding_length,
        gff_filename,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))
}


// PyO3 module definition
#[pymodule]
fn helixerpost(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_world, m)?)?;
    m.add_function(wrap_pyfunction!(run_helixer_post, m)?)?;
    Ok(())
}
