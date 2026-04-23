use actix_web::rt::time::sleep;
use awc::Client;
use rand::RngExt;
use std::time::Duration;

#[actix_web::main]
async fn main() {
    let client = Client::new();
    let mut rng = rand::rng();

    loop {
        let size = rng.random_range(1..=64);
        let mut body = Vec::with_capacity(size);
        for _ in 0..size {
            body.push(rng.random());
        }

        let _ = client
            .post("http://localhost:80")
            .insert_header(("Content-Type", "application/octet-stream"))
            .send_body(body)
            .await;

        sleep(Duration::from_millis(50)).await;
    }
}
