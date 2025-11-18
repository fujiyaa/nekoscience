use rosu_pp::{Beatmap, Difficulty, Performance};

pub struct PerfectSliders {
    pub osu_large_tick_hits: u32,
    pub osu_small_tick_hits: u32,
    pub slider_end_hits: u32,
}

pub fn calculate_perfect_sliders(map: &Beatmap) -> PerfectSliders {
    let difficulty = Difficulty::new().calculate(map);

    let max_combo = difficulty.max_combo();

    let mut performance = Performance::new(difficulty)
        .combo(max_combo)
        .accuracy(100.0)
        .misses(0);

    let state = performance.generate_state();
    
    PerfectSliders {
        osu_large_tick_hits: state.osu_large_tick_hits,
        osu_small_tick_hits: state.osu_small_tick_hits,
        slider_end_hits: state.slider_end_hits,
    }
}

#[allow(unused)]
pub fn calculate_sliders_with_score(
    map: &Beatmap,
    n300: u32,
    n100: u32,
    n50: u32,
    misses: u32,
    accuracy: f64,
) -> PerfectSliders {
    let difficulty = Difficulty::new().calculate(map);

    let max_combo = difficulty.max_combo();

    let mut performance = Performance::new(difficulty)
        .combo(max_combo)     
        .n300(n300)
        .n100(n100)
        .n50(n50)
        .misses(misses)
        .accuracy(accuracy);

    let state = performance.generate_state();

    PerfectSliders {
        osu_large_tick_hits: state.osu_large_tick_hits,
        osu_small_tick_hits: state.osu_small_tick_hits,
        slider_end_hits: state.slider_end_hits,
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use rosu_pp::Beatmap;

    #[test]
    fn test_perfect_state() {
        let map_path = r"E:\fa\nekoscience\bot\src\cache\beatmaps\9910.osu";
        let map = Beatmap::from_path(map_path).unwrap();

        let state = calculate_perfect_sliders(&map);

        println!(
            "Perfect state: osu_large_tick_hits={}, osu_small_tick_hits={}, nslider_end_hits={}",
            state.osu_large_tick_hits, state.osu_small_tick_hits, state.slider_end_hits
        );         
    }

    #[test]
    fn test_custom_score_sliders() {
        let map_path = r"E:\fa\nekoscience\bot\src\cache\beatmaps\1580334.osu";
        let map = Beatmap::from_path(map_path).unwrap();

        let custom_state = calculate_sliders_with_score(&map, 120, 0, 0, 0, 90.5);

        println!(
            "Custom state: osu_large_tick_hits={}, osu_small_tick_hits={}, slider_end_hits={}",
            custom_state.osu_large_tick_hits, custom_state.osu_small_tick_hits, custom_state.slider_end_hits
        );
    }

    //damn
}
