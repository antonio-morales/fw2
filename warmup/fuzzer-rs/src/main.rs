use anyhow::{anyhow, Result};
use clap::Parser;
use futures::stream::{self, StreamExt};
use reqwest::{Client, Method};
use std::path::PathBuf;
use std::time::{Duration, Instant};
use tokio::fs;

/// Async HTTP fuzzer for localhost targets.
///
/// Substitutes each wordlist entry into the URL template at the FUZZ marker,
/// fires requests concurrently, and prints a compact per-hit line.
#[derive(Parser, Debug)]
#[command(name = "fuzzer-rs", version, about)]
struct Args {
    /// URL template. Use FUZZ as the substitution marker.
    /// e.g. http://127.0.0.1:8080/FUZZ
    #[arg(short = 'u', long)]
    url: String,

    /// Path to newline-delimited wordlist.
    #[arg(short = 'w', long)]
    wordlist: PathBuf,

    /// HTTP method.
    #[arg(short = 'X', long, default_value = "GET")]
    method: String,

    /// Concurrent in-flight requests.
    #[arg(short = 'c', long, default_value_t = 50)]
    concurrency: usize,

    /// Per-request timeout (seconds).
    #[arg(short = 't', long, default_value_t = 5)]
    timeout: u64,

    /// Comma-separated status codes to hide (e.g. 404,403).
    #[arg(long, default_value = "")]
    hide_status: String,

    /// Optional JSON body template (FUZZ substituted if present).
    #[arg(long)]
    body: Option<String>,

    /// Extra header, repeatable. Format: "Name: Value".
    #[arg(short = 'H', long = "header")]
    headers: Vec<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    if !args.url.contains("FUZZ") && args.body.as_deref().map_or(true, |b| !b.contains("FUZZ")) {
        return Err(anyhow!("url or body must contain the FUZZ marker"));
    }

    let raw = fs::read_to_string(&args.wordlist).await?;
    let words: Vec<String> = raw
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#'))
        .map(str::to_owned)
        .collect();

    let hide: Vec<u16> = args
        .hide_status
        .split(',')
        .filter_map(|s| s.trim().parse::<u16>().ok())
        .collect();

    let method = Method::from_bytes(args.method.to_uppercase().as_bytes())
        .map_err(|_| anyhow!("invalid HTTP method"))?;

    let client = Client::builder()
        .timeout(Duration::from_secs(args.timeout))
        .danger_accept_invalid_certs(true)
        .build()?;

    let total = words.len();
    let start = Instant::now();
    println!(
        "fuzzer-rs → {} {} ({} words, conc={})",
        args.method, args.url, total, args.concurrency
    );

    let headers = args.headers.clone();
    let body_tpl = args.body.clone();
    let url_tpl = args.url.clone();

    let results = stream::iter(words.into_iter().enumerate())
        .map(|(_, w)| {
            let client = client.clone();
            let method = method.clone();
            let url = url_tpl.replace("FUZZ", &w);
            let body = body_tpl.as_ref().map(|b| b.replace("FUZZ", &w));
            let headers = headers.clone();
            async move {
                let t0 = Instant::now();
                let mut req = client.request(method, &url);
                for h in &headers {
                    if let Some((k, v)) = h.split_once(':') {
                        req = req.header(k.trim(), v.trim());
                    }
                }
                if let Some(b) = body {
                    req = req.header("content-type", "application/json").body(b);
                }
                match req.send().await {
                    Ok(resp) => {
                        let status = resp.status().as_u16();
                        let bytes = resp.bytes().await.map(|b| b.len()).unwrap_or(0);
                        let dur = t0.elapsed().as_millis();
                        (w, Some((status, bytes, dur)))
                    }
                    Err(e) => {
                        eprintln!("  err {w}: {e}");
                        (w, None)
                    }
                }
            }
        })
        .buffer_unordered(args.concurrency);

    let mut shown = 0usize;
    let mut done = 0usize;
    tokio::pin!(results);
    while let Some((word, outcome)) = results.next().await {
        done += 1;
        if let Some((status, bytes, dur)) = outcome {
            if !hide.contains(&status) {
                println!("  {status}  {bytes:>7}B  {dur:>4}ms  {word}");
                shown += 1;
            }
        }
    }

    let elapsed = start.elapsed().as_secs_f64();
    let rps = if elapsed > 0.0 { done as f64 / elapsed } else { 0.0 };
    println!(
        "\ndone → {done}/{total} requests, {shown} shown, {elapsed:.1}s, {rps:.1} req/s"
    );
    Ok(())
}
