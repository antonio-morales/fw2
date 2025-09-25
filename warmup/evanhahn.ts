const METHODS = [
  "GET",
  "POST",
  "PUT",
  "DELETE",
  "PATCH",
  "HEAD",
] as const;

const random = (min: number, max: number): number => (
  Math.floor(Math.random() * (max - min)) + min
);

const randomBytes = (minLength: number, maxLength: number): Uint8Array => {
  const result = new Uint8Array(random(minLength, maxLength));
  return crypto.getRandomValues(result);
};

const randomString = (minLength: number, maxLength: number): string => {
  return new TextDecoder().decode(randomBytes(minLength, maxLength));
};

const randomElement = <T>(arr: ReadonlyArray<T>): T => {
  return arr[random(0, arr.length)];
};

export function makeRandomRequest(): Request {
  const pathname = "/" + randomString(0, 64);
  return new Request(
    new URL(
      pathname,
      "http://localhost:8000/",
    ),
    { method: randomElement(METHODS) },
  );
}

await fetch(makeRandomRequest());
