use rosu_pp::{Beatmap, Difficulty, Performance};

pub struct PerfectHits {
    pub n300: u32,
    pub n100: u32,
    pub n50: u32,
    pub misses: u32,
    pub max_combo: u32,
}

pub fn calculate_perfect_hits(map: &Beatmap) -> PerfectHits {
    let difficulty = Difficulty::new().calculate(map);

    let max_combo = difficulty.max_combo();

    let mut performance = Performance::new(difficulty)
        .combo(max_combo)
        .accuracy(100.0)
        .misses(0);

    let state = performance.generate_state();
    
    PerfectHits {
        n300: state.n300,
        n100: state.n100,
        n50: state.n50,
        misses: state.misses,
        max_combo: state.max_combo,
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

        let state = calculate_perfect_hits(&map);

        println!(
            "Perfect state: n300={}, n100={}, n50={}, misses={}, max_combo={}",
            state.n300, state.n100, state.n50, state.misses, state.max_combo
        );

        assert_eq!(state.misses, 0);
        assert_eq!(state.n50, 0);
    }
}
