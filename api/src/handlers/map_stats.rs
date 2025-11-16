use axum::{Json, extract::Json as AxumJson};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use crate::utils::mods_parser;

#[derive(Deserialize)]
pub struct PpRequest {
    pub map_path: String, 

    pub n300: Option<u32>, 
    pub n100: Option<u32>,
    pub n50: Option<u32>,
    pub misses: Option<u32>,

    pub mods: Option<String>, 
    pub combo: Option<u32>,
    pub accuracy: Option<f64>,

    pub lazer: Option<bool>,
    pub clock_rate: Option<f64>, 

    pub custom_ar: Option<f32>,
    pub custom_cs: Option<f32>,
    pub custom_hp: Option<f32>,
    pub custom_od: Option<f32>,
}

#[derive(Serialize, Default)]
pub struct PpResponse {
    pub pp: f64,
    pub no_choke_pp: f64,
    pub perfect_pp: f64,

    pub star_rating: f64,
    pub perfect_combo: u32,
    pub expected_bpm: f64,

    pub n300: u32,
    pub n100: u32,
    pub n50: u32,
    pub misses: u32,
}

pub async fn calculate_map_stats(
    AxumJson(payload): AxumJson<PpRequest>
) -> Json<PpResponse> {
    let base_folder = r"E:\fa\nekoscience\bot\src\cache\beatmaps";

    let mut map_path = PathBuf::from(base_folder);
    map_path.push(format!("{}.osu", payload.map_path));

    let map = match rosu_pp::Beatmap::from_path(&map_path) {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Failed to load beatmap from {}: {:?}", map_path.display(), e);
            return Json(PpResponse::default());
        }
    };

    if let Err(e) = map.check_suspicion() {
        eprintln!("Beatmap suspicion check failed for {}: {:?}", map_path.display(), e);
        return Json(PpResponse::default());
    }

    let mods_str = payload.mods.unwrap_or("NM".to_string());
    let mods = mods_parser::mods_from_str(&mods_str);
    let clock_rate = payload.clock_rate.unwrap_or(1.0);
    let lazer = payload.lazer.unwrap_or(true);

    let ar = payload.custom_ar.unwrap_or(0.0);
    let cs = payload.custom_cs.unwrap_or(0.0);
    let hp = payload.custom_hp.unwrap_or(0.0);
    let od = payload.custom_od.unwrap_or(0.0);

    // Calculate difficulty attributes
    let mut difficulty = rosu_pp::Difficulty::new()
    .lazer(lazer)
    .cs(cs, false)
    .ar(ar, false)
    .od(od, false)
    .hp(hp, false)
    .mods(mods);

    if clock_rate != 1.0 {
        difficulty = difficulty.clock_rate(clock_rate);
    }

    let diff_attrs = difficulty.calculate(&map);


    let star_rating = diff_attrs.stars();
    let max_combo = diff_attrs.max_combo();

    // Calculate performance attributes
    let mut performance = rosu_pp::Performance::new(diff_attrs)
    
    .lazer(lazer)
    .combo(payload.combo.unwrap_or(max_combo))
    .misses(payload.misses.unwrap_or(0))
    .accuracy(payload.accuracy.unwrap_or(100.0));

    if clock_rate != 1.0 {
        performance = performance.clock_rate(clock_rate);
    }

    let perf_attrs = performance.clone().calculate();

    let pp = perf_attrs.pp();

    let state = performance.generate_state();

    let perf_attrs = performance.calculate();

    let n300 = state.n300;
    let n100 = state.n100;
    let n50 = state.n50;
    let misses = state.misses;
    let max_combo = state.max_combo;

    let mut perfect_performance = perf_attrs.clone().performance()
        .lazer(lazer);

    if clock_rate != 1.0 {
        perfect_performance = perfect_performance.clock_rate(clock_rate);
    }

    let perfect_pp = perfect_performance.calculate().pp();

  
    let mut no_choke_performance = perf_attrs.performance()
        .mods(mods)        
        .accuracy(payload.accuracy.unwrap_or(100.0))
        .lazer(lazer)
        .n300(payload.n300.unwrap_or(0) + payload.misses.unwrap_or(0))
        .n100(payload.n100.unwrap_or(0))
        .n50(payload.n50.unwrap_or(0))
        .misses(0);

    if clock_rate != 1.0 {
        no_choke_performance = no_choke_performance.clock_rate(clock_rate);
    }

    let no_choke_pp = no_choke_performance.calculate().pp();

    let perfect_combo = max_combo;
    let expected_bpm = map.bpm() as f64;

    // println!("Lazer: {:?}", lazer);

    Json(PpResponse {
        pp,
        no_choke_pp,
        perfect_pp,

        star_rating,      
        perfect_combo,
        expected_bpm,

        n300,
        n100,
        n50,
        misses,
    })
}
