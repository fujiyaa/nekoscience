use std::collections::HashMap;

pub fn mods_from_str(s: &str) -> u32 {
    let s = s.to_uppercase();

    let map: HashMap<&'static str, u32> = HashMap::from([
        ("NF", 1),
        ("EZ", 2),
        ("TD", 4),
        ("HD", 8),
        ("HR", 16),
        ("SD", 32),
        ("DT", 64),
        ("RX", 128),
        ("HT", 256),
        ("NC", 512),
        ("FL", 1024),
        ("AT", 2048),
        ("SO", 4096),
        ("AP", 8192),
        ("PF", 16384),
        ("K4", 32768),
        ("K5", 65536),
        ("K6", 131072),
        ("K7", 262144),
        ("K8", 524288),
        ("FI", 1048576),
        ("RD", 2097152),
        ("CM", 4194304),
        ("TP", 8388608),
        ("K9", 16777216),
        ("KO", 33554432),
        ("K1", 67108864),
        ("K3", 134217728),
        ("K2", 268435456),
        ("SV2", 536870912),
        ("MR", 1073741824),
    ]);

    let mut bits: u32 = 0;

    let chars: Vec<char> = s.chars().collect();
    let mut i = 0;

    while i + 1 < chars.len() {
        let pair = format!("{}{}", chars[i], chars[i + 1]);

        if let Some(value) = map.get(pair.as_str()) {
            bits |= value;

            if pair == "NC" {
                bits |= 64;
            }

            if pair == "PF" {
                bits |= 32;
            }

            i += 2;
        } else {
            i += 1;
        }
    }

    bits
}
