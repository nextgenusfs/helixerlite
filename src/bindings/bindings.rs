use helixer_post::main;
use pyo3::{prelude::*, PyAny};

#[pyfunction]
fn main_py() -> PyResult<()> {
    let result = main();
    if let Ok(_) = result {
        Ok(())
    } else {
        Err(PyRuntimeError::new_err("Rust error"))
    }
}

#[init_lib(helixerlite)]
fn helixer_post_bin(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(main_py, m)?)?;
    Ok(())
}