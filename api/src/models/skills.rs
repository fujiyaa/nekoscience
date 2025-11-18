use std::collections::HashMap;
use crate::utils::mods_parser;
use rosu_pp::{Beatmap};
use rosu_pp::{
    osu::{OsuPerformance, OsuScoreState},
    taiko::{TaikoPerformance, TaikoScoreState},
    catch::{CatchPerformance, CatchScoreState, CatchPerformanceAttributes},
    mania::{ManiaPerformance, ManiaScoreState},
};
use super::score::Score;

#[derive(Clone, Copy)]
pub enum GameMode {
    Osu,
    Taiko,
    Catch,
    Mania,
}

impl GameMode {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "osu" => Some(GameMode::Osu),
            "taiko" => Some(GameMode::Taiko),
            "catch" => Some(GameMode::Catch),
            "mania" => Some(GameMode::Mania),
            _ => None,
        }
    }
}
#[derive(Debug)]
pub enum Skills {
    Osu { acc: f64, aim: f64, speed: f64, acc_total: f64, aim_total: f64, speed_total: f64 },
    Taiko { acc: f64, strain: f64 },
    Catch { acc: f64, movement: f64 },
    Mania { acc: f64, strain: f64 },
}

fn estimate_slider_hits(n300: u32, n100: u32, n50: u32, misses: u32, accuracy: f64) -> (u32, u32, u32) {
    let total_hits = n300 + n100 + n50 + misses;
    let acc_ratio = (accuracy / 100.0).clamp(0.0, 1.0);
    let slider_end_hits = ((n300 as f64 + n100 as f64 * 0.5) * acc_ratio).round() as u32;
    let large_tick_hits = ((total_hits - slider_end_hits) as f64 * 0.7 * acc_ratio).round() as u32;
    let small_tick_hits = ((total_hits - slider_end_hits - large_tick_hits) as f64 * 0.5 * acc_ratio).round() as u32;
    (slider_end_hits, large_tick_hits, small_tick_hits)
}

impl Skills {
    pub fn calculate(mode: GameMode, scores: &[Score], mut maps: HashMap<u32, Beatmap>) -> Self {
        
        let map_val = |val: f64| {
            let factor = (8.0 / (val / 72.0 + 8.0)).powi(10);
            -101.0 * factor + 101.0
        };

        match mode {
            GameMode::Osu => {
                let mut acc = 0.0;
                let mut aim = 0.0;
                let mut speed = 0.0;
                let mut weight_sum = 0.0;
                const ACC_NERF: f64 = 1.1;
                const AIM_NERF: f64 = 3.7;
                const SPEED_NERF: f64 = 2.5;
                let mut last_weight = 0.0;

                for (i, score) in scores.iter().enumerate() {
                    let Some(beatmap) = maps.remove(&score.map_id) else { continue; };

                    let (slider_end_hits, large_tick_hits, small_tick_hits) = estimate_slider_hits(
                        score.statistics.great,
                        score.statistics.ok,
                        score.statistics.meh,
                        score.statistics.miss,
                        score.accuracy,
                    );

                    // let slider_end_hits = score.statistics.slider_tail_hit;
                    // let large_tick_hits= score.statistics.large_tick_hit;
                    // let small_tick_hits = score.statistics.small_tick_hit;

                    let state = OsuScoreState {
                        max_combo: score.max_combo,
                        n300: score.statistics.great,
                        n100: score.statistics.ok,
                        n50: score.statistics.meh,
                        misses: score.statistics.miss,
                        slider_end_hits,
                        large_tick_hits,
                        small_tick_hits,
                    };

                    let mods = mods_parser::mods_from_str(&score.mods);

                    let attrs = OsuPerformance::try_new(beatmap)
                        .unwrap()
                        .mods(mods)
                        .state(state)
                        .lazer(score.set_on_lazer)
                        .calculate()
                        .unwrap();

                    let acc_val = attrs.pp_acc / ACC_NERF;
                    let aim_val = attrs.pp_aim / AIM_NERF;
                    let speed_val = attrs.pp_speed / SPEED_NERF;
                    let weight = 0.95_f64.powi(i as i32);

                    acc += acc_val * weight;
                    aim += aim_val * weight;
                    speed += speed_val * weight;
                    weight_sum += weight;
                    last_weight = weight;
                }

                let acc_total = acc * last_weight;
                let aim_total = aim * last_weight;
                let speed_total = speed * last_weight;

                acc = map_val(acc / weight_sum);
                aim = map_val(aim / weight_sum);
                speed = map_val(speed / weight_sum);

                Self::Osu { acc, aim, speed, acc_total, aim_total, speed_total }
            }

            GameMode::Taiko => {
                let mut acc = 0.0;
                let mut strain = 0.0;
                let mut weight_sum = 0.0;
                const ACC_NERF: f64 = 1.15;
                const DIFFICULTY_NERF: f64 = 3.6;

                for (i, score) in scores.iter().enumerate() {
                    let Some(attrs) = maps.remove(&score.map_id) else { continue; };

                    let state = TaikoScoreState {
                        max_combo: score.max_combo,
                        n300: score.statistics.great,
                        n100: score.statistics.ok,
                        misses: score.statistics.miss,
                    };

                    let mods = mods_parser::mods_from_str(&score.mods);

                    let difficulty = rosu_pp::Difficulty::new()
                        .mods(mods)
                        .lazer(score.set_on_lazer)
                        .calculate(&attrs);

                    let attrs = TaikoPerformance::try_new(difficulty)
                        .unwrap()
                        .mods(mods)
                        .state(state)
                        .calculate()
                        .unwrap();

                    let acc_val = attrs.pp_acc / ACC_NERF;
                    let diff_val = attrs.pp_difficulty / DIFFICULTY_NERF;
                    let weight = 0.95_f64.powi(i as i32);

                    acc += acc_val * weight;
                    strain += diff_val * weight;
                    weight_sum += weight;
                }

                acc = map_val(acc / weight_sum);
                strain = map_val(strain / weight_sum);

                Self::Taiko { acc, strain }
            }

            GameMode::Catch => {
                let mut acc = 0.0;
                let mut movement = 0.0;
                let mut weight_sum = 0.0;
                const ACC_BUFF: f64 = 1.7;
                const MOVEMENT_NERF: f64 = 5.1;

                for (i, score) in scores.iter().enumerate() {
                    let Some(attrs) = maps.remove(&score.map_id) else { continue; };

                    let state = CatchScoreState {
                        max_combo: score.max_combo,
                        fruits: score.statistics.great,
                        droplets: score.statistics.large_tick_hit,
                        tiny_droplets: score.statistics.small_tick_hit,
                        tiny_droplet_misses: score.statistics.small_tick_miss,
                        misses: score.statistics.miss,
                    };

                    let mods = mods_parser::mods_from_str(&score.mods);

                    let difficulty = rosu_pp::Difficulty::new()
                        .mods(mods)
                        .lazer(score.set_on_lazer)
                        .calculate(&attrs);

                    let od = attrs.od as f64;
                    let attrs = CatchPerformance::try_new(difficulty)
                        .unwrap()
                        .mods(mods)
                        .state(state)
                        .calculate()
                        .unwrap();

                    let CatchPerformanceAttributes { difficulty, pp } = attrs;
                    let acc_ = score.accuracy.max(10.0) as f64;
                    let n_objects = (difficulty.n_fruits + difficulty.n_droplets + difficulty.n_tiny_droplets) as f64;
                    let acc_exp = ((acc_ / 46.5).powi(6) / 55.0).powf(1.5);
                    let acc_adj = (5.0 * acc_exp.powf(0.1).ln_1p()).recip();
                    let acc_val = difficulty.stars.powf(acc_exp - acc_adj) * (od / 7.0).powf(0.25) * (n_objects / 2000.0).powf(0.15) * ACC_BUFF;

                    let movement_val = pp / MOVEMENT_NERF;
                    let weight = 0.95_f64.powi(i as i32);

                    acc += acc_val * weight;
                    movement += movement_val * weight;
                    weight_sum += weight;
                }

                acc = map_val(acc / weight_sum);
                movement = map_val(movement / weight_sum);

                Self::Catch { acc, movement }
            }

            GameMode::Mania => {
                let mut acc = 0.0;
                let mut strain = 0.0;
                let mut weight_sum = 0.0;
                const ACC_BUFF: f64 = 2.1;
                const DIFFICULTY_NERF: f64 = 5.0;

                for (i, score) in scores.iter().enumerate() {
                    let Some(beatmap) = maps.remove(&score.map_id) else { continue; };

                    let state = ManiaScoreState {
                        n320: score.statistics.perfect,
                        n300: score.statistics.great,
                        n200: score.statistics.good,
                        n100: score.statistics.ok,
                        n50: score.statistics.meh,
                        misses: score.statistics.miss,
                    };

                    let mods = mods_parser::mods_from_str(&score.mods);

                    let difficulty = rosu_pp::Difficulty::new()
                        .mods(mods)
                        .lazer(score.set_on_lazer)
                        .calculate(&beatmap);

                    let attrs = ManiaPerformance::try_new(difficulty)
                        .unwrap()
                        .mods(mods)
                        .lazer(score.set_on_lazer)
                        .state(state)
                        .calculate()
                        .unwrap();

                    let acc_ = ((score.accuracy / 36.0).powf(4.5) / 60.0).powf(1.5);
                    let od = beatmap.od as f64;
                    let n_objects = score.total_hits() as f64;
                    let acc_val = attrs.stars().powf(acc_) * (od / 7.0).powf(0.25) * (n_objects / 2000.0).powf(0.15) * ACC_BUFF;
                    let diff_val = attrs.pp_difficulty / DIFFICULTY_NERF;
                    let weight = 0.95_f64.powi(i as i32);

                    acc += acc_val * weight;
                    strain += diff_val * weight;
                    weight_sum += weight;
                }

                acc = map_val(acc / weight_sum);
                strain = map_val(strain / weight_sum);

                Self::Mania { acc, strain }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    use crate::models::score::{Score, ScoreStatistics};
    
    fn dummy_score_map_id_9910(id: u32) -> Score {
        Score {
            map_id: id,
            max_combo: 189,
            accuracy: 100.0,
            mods: String::new(),
            set_on_lazer: false,
            statistics: ScoreStatistics {
                great: 139,
                ok: 0,
                meh: 0,
                miss: 0,
                large_tick_hit: 0,
                small_tick_hit: 0,
                small_tick_miss: 0,
                slider_tail_hit: 0,
                good: 0,
                perfect: 0,
            },
        }
    }
    
    #[test]
    fn test_skills_real_map() {
        let score = dummy_score_map_id_9910(9910);
        
        let mut maps = HashMap::new();
        
        let map_path = r"E:\fa\nekoscience\bot\src\cache\beatmaps\9910.osu";
        let map = Beatmap::from_path(map_path).unwrap();

        maps.insert(9910, map);

        let skills = Skills::calculate(GameMode::Osu, &[score], maps);

        match skills {
            Skills::Osu { acc, aim, speed, acc_total, aim_total, speed_total } => {
                println!(
                "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10}",
                "acc", "aim", "speed", "acc_total", "aim_total", "speed_total"
            );
            println!("{}", "-".repeat(60)); 

            println!(
                "{:<10.2} {:<10.2} {:<10.2} {:<10.2} {:<10.2} {:<10.2}",
                acc, aim, speed, acc_total, aim_total, speed_total
            );
        }
            _ => println!("Skills is not Osu variant"),        }


        match skills {
            Skills::Osu { acc, aim, speed, acc_total, aim_total, speed_total } => {
                
                assert!(acc > 0.0, "damn");
                assert!(aim > 0.0, "damn");
                assert!(speed > 0.0, "damn");

                assert!(acc_total > 0.0);
                assert!(aim_total > 0.0);
                assert!(speed_total > 0.0);
            }
            _ => panic!("Skills::calculate err"),
        }
    }
}

