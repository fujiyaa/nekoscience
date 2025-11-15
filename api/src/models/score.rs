use serde::Deserialize;

#[derive(Deserialize)]
pub struct ScoreInput {
    pub map_id: u32,
    pub n320: Option<u32>,
    pub n300: Option<u32>,
    pub n200: Option<u32>,
    pub n100: Option<u32>,
    pub n50: Option<u32>,
    pub misses: Option<u32>,
    pub combo: Option<u32>,
    pub mods: Option<String>,
    pub accuracy: Option<f64>,
    pub set_on_lazer: Option<bool>,
    pub large_tick_hit: Option<u32>,
    pub small_tick_hit: Option<u32>,
    pub small_tick_miss: Option<u32>,
    pub slider_tail_hit: Option<u32>,
}

#[allow(unused)]
#[derive(Clone)]
pub struct ScoreStatistics {
    pub perfect: u32,      
    pub great: u32,        
    pub good: u32,         
    pub ok: u32,           
    pub meh: u32,          
    pub miss: u32,
    pub large_tick_hit: u32,
    pub small_tick_hit: u32,
    pub small_tick_miss: u32,
    pub slider_tail_hit: u32,
}

#[derive(Clone)]
pub struct Score {
    pub map_id: u32,
    pub max_combo: u32,
    pub mods: String,
    pub accuracy: f64,
    pub statistics: ScoreStatistics,
    pub set_on_lazer: bool,
}

impl Score {
    pub fn total_hits(&self) -> u32 {
        self.statistics.perfect
            + self.statistics.great
            + self.statistics.good
            + self.statistics.ok
            + self.statistics.meh
            + self.statistics.miss // исправлено
    }
}

pub fn to_score(input: &ScoreInput) -> Score {
    Score {
        map_id: input.map_id,
        max_combo: input.combo.unwrap_or(0),
        mods: input.mods.clone().unwrap_or_else(|| "NM".to_string()),
        accuracy: input.accuracy.unwrap_or(100.0),
        statistics: ScoreStatistics {
            perfect: input.n320.unwrap_or(0),
            great: input.n300.unwrap_or(0),
            good: input.n200.unwrap_or(0),
            ok: input.n100.unwrap_or(0),
            meh: input.n50.unwrap_or(0),
            miss: input.misses.unwrap_or(0),
            large_tick_hit: input.large_tick_hit.unwrap_or(0),
            small_tick_hit: input.small_tick_hit.unwrap_or(0),
            small_tick_miss: input.small_tick_miss.unwrap_or(0),
            slider_tail_hit: input.slider_tail_hit.unwrap_or(0),
        },
        set_on_lazer: input.set_on_lazer.unwrap_or(true),
    }
}
