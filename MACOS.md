# running the workshop on macOS

notes on getting everything working on a mac (tested on apple silicon,
macOS 15). the devcontainer is the official path, but if you'd rather run
natively, here's what worked for me.

## prereqs

```bash
# java 21 for exercise 1
brew install openjdk@21
export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"

# node 18.19.1 via nvm for exercises 2 and 3
brew install nvm
mkdir -p ~/.nvm && echo 'source $(brew --prefix nvm)/nvm.sh' >> ~/.zshrc
source ~/.zshrc
nvm install 18.19.1
nvm use 18.19.1
```

sanity check:

```bash
java --version    # openjdk 21.x
node --version    # v18.19.1
npm --version     # 10.x (fine, >= 9.2.0)
```

## exercise 1 (BookingForm + Jazzer)

the tricky part: the bundled `exercise1/jazzer/jazzer` binary is
**linux x86-64 only**. on apple silicon it won't run.

three options:

**a. use the devcontainer** — open the repo in vs code with the Dev
Containers extension, or launch a codespace. everything is preinstalled.
easiest path.

**b. run jazzer in docker** — quick, no vs code needed:

```bash
cd exercise1
javac BookingForm.java fuzzer.java
docker run --rm -it --platform linux/amd64 \
  -v "$PWD":/work -w /work \
  eclipse-temurin:21-jdk bash -c "./jazzer/jazzer --target_class=fuzzer corpus"
```

**c. verify the crash without jazzer** — since you still have java
natively, you can confirm any suspect input directly:

```java
// save as Crash.java next to BookingForm.java
public class Crash {
  public static void main(String[] a) { BookingForm.parseBooking(a[0]); }
}
```

```bash
javac BookingForm.java Crash.java
java Crash 'A;B;a@b.c;single;1;2025-01-01T00:00;Sep 5 2025;false;'
```

## exercise 2 (moment.js + Jazzer.js)

the `exercise2` folder doesn't ship with a `package.json`. add one:

```bash
cd exercise2
cat > package.json <<'EOF'
{
  "name": "ex2",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "moment": "2.15.1",
    "@jazzer.js/core": "^2.0.0"
  }
}
EOF
npm install
```

run the fuzzer:

```bash
npx jazzer fuzzer.js fuzz
```

jazzer.js is pure js so no linux-binary issue here — it runs fine on mac.

## exercise 3

same node setup as exercise 2. add a `package.json` inside `exercise3/`
with whatever deps the harness requires, then `npm install` and run the
jazzer.js harness.

## common gotchas

- `java --version` showing "unable to locate a java runtime": you didn't
  `export PATH=...openjdk@21/bin:$PATH`. brew's keg-only install doesn't
  link openjdk@21 by default.
- `npm WARN deprecated` noise on `npm install moment@2.15.1` is expected
  — this version is intentionally old to reproduce the ReDoS.
- jazzer binary prints `bad CPU type in executable` or silently does
  nothing on apple silicon. you need docker or the devcontainer.
