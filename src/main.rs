use pyo3::prelude::*;
use helixer_post_bin::analysis::extractor::{BasePredictionExtractor, ComparisonExtractor};
use helixer_post_bin::analysis::hmm::show_hmm_config;
use helixer_post_bin::analysis::rater::SequenceRating;
use helixer_post_bin::analysis::Analyzer;
use helixer_post_bin::gff::GffWriter;
use helixer_post_bin::results::raw::RawHelixerPredictions;
use helixer_post_bin::results::HelixerResults;
use std::fs::File;
use std::io::BufWriter;
use std::path::Path;
use std::process::exit;

/// A Python function that wraps the main functionality
#[pyfunction]
fn run_helixer_post(
    genome_path: &str,
    predictions_path: &str,
    window_size: usize,
    edge_threshold: f64,
    peak_threshold: f64,
    min_coding_length: usize,
    gff_filename: &str,
) -> PyResult<()> {
    let helixer_res = HelixerResults::new(predictions_path.as_ref(), genome_path.as_ref())
        .expect("Failed to open input files");

    let bp_extractor = BasePredictionExtractor::new_from_prediction(&helixer_res)
        .expect("Failed to open Base / ClassPrediction / PhasePrediction Datasets");

    let comp_extractor = ComparisonExtractor::new(&helixer_res)
        .expect("Failed to open ClassReference / PhaseReference / ClassPrediction / PhasePrediction Datasets");

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

    show_hmm_config();

    let gff_file = File::create(gff_filename).unwrap();
    let mut gff_writer = GffWriter::new(BufWriter::new(gff_file));

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
        println!(
            "Sequences for Species {} - {}",
            species.get_name(),
            id.inner()
        );
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

        println!(
            "Forward for Species {} - {}",
            species.get_name(),
            id.inner()
        );
        fwd_species_rating.dump(analyzer.has_ref());

        println!(
            "Reverse for Species {} - {}",
            species.get_name(),
            id.inner()
        );
        rev_species_rating.dump(analyzer.has_ref());

        let mut species_rating = SequenceRating::new();
        species_rating.accumulate(&fwd_species_rating);
        species_rating.accumulate(&rev_species_rating);

        println!("Total for Species {} - {}", species.get_name(), id.inner());
        species_rating.dump(analyzer.has_ref());
    }

    println!("Total: {}bp across {} windows", total_length, total_count);
    Ok(())
}

/// A module definition for PyO3
#[pymodule]
fn helixerlite(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_helixer_post, m)?)?;
    Ok(())
}