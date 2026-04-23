# exercise 1 — findings

found an `ArrayIndexOutOfBoundsException` in `BookingForm.parseDate` when the
departure date uses the text pattern (`Month DD YYYY`) and the month name
doesn't match any entry in the `months` array.

## root cause

`BookingForm.java` line ~140:

```java
String[] months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept, Oct", "Nov", "Dec" };
```

there's a typo — `"Sept, Oct"` is one string instead of two, so the array has
**11** elements, not 12. but the lookup loop iterates `i < 12`:

```java
for (int i = 0; i < 12; i++) {
  if (monthName.equalsIgnoreCase(months[i])) { ... break; }
}
```

if the month name doesn't match anything, `i` reaches 11 and `months[11]`
throws `ArrayIndexOutOfBoundsException: Index 11 out of bounds for length 11`.

## repro

```bash
cd exercise1
javac BookingForm.java fuzzer.java
java -cp jazzer/jazzer_standalone.jar:. com.code_intelligence.jazzer.Jazzer \
  --target_class=fuzzer corpus val/
```

the file `val/crash_input.txt` triggers the crash on first run.

content:

```
A;B;a@b.c;single;1;2025-01-01T00:00;Sep 5 2025;false;
```

the departure field `Sep 5 2025` matches the text regex but "Sep" isn't in
the months array (only "Sept, Oct" is) so the loop walks off the end.

## fix suggestion

```java
String[] months = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
```

also worth bounding the loop to `months.length` rather than the magic `12`.
