use rand::{Rng, seq::SliceRandom};
use reqwest::{Client, Method};
use std::time::Duration;

const TARGET: &str = "http://localhost:8000"; // Change to your target URL
const ITERATIONS: usize = 100;

fn random_method() -> Method {
    let methods = [
        Method::GET,
        Method::POST,
        Method::PUT,
        Method::DELETE,
        Method::PATCH,
        Method::OPTIONS,
        Method::HEAD,
    ];
    methods.choose(&mut rand::thread_rng()).unwrap().clone()
}

fn random_headers() -> Vec<(String, String)> {
    let mut rng = rand::thread_rng();
    let headers = [
        ("User-Agent", "Mozilla/5.0"),
        ("X-Fuzz", "true"),
        ("Accept", "*/*"),
        ("Cookie", "ID=deadbeef"),
    ];

    // Randomly select 1-4 headers
    let count = rng.gen_range(1..=headers.len());
    headers
        .choose_multiple(&mut rng, count)
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

fn random_body() -> Option<String> {
    let mut rng = rand::thread_rng();
    if rng.gen_bool(0.5) {
        let len = rng.gen_range(5..30);
        Some(
            (0..len)
                .map(|_| rng.sample(rand::distributions::Alphanumeric) as char)
                .collect(),
        )
    } else {
        None
    }
}

#[tokio::main]
async fn main() {
    let client = Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .unwrap();

    for i in 0..ITERATIONS {
        let method = random_method();
        let headers = random_headers();
        let body = random_body();

        let mut req = client.request(method.clone(), TARGET);
        for (k, v) in headers {
            req = req.header(k, v);
        }
        if let Some(b) = &body {
            req = req.body(b.clone());
        }

        println!("\n=== Iteration {} ===", i + 1);
        println!("Method: {:?}", method);
        if let Some(b) = &body {
            println!("Body: {}", b);
        }

        match req.send().await {
            Ok(resp) => {
                println!("Status: {}", resp.status());
                let text = resp.text().await.unwrap_or_else(|_| "<error>".to_string());
                println!("Response: {}", text);
            }
            Err(e) => {
                println!("Request error: {}", e);
            }
        }
    }
}
