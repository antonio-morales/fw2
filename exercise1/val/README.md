# exercise 1

found a crash in BookingForm.parseDate. the months array has a typo:

```java
String[] months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept, Oct", "Nov", "Dec" };
```

"Sept, Oct" is one string (quoted together), so the array only has 11
elements instead of 12. the loop right below it iterates `i < 12`:

```java
for (int i = 0; i < 12; i++) {
  if (monthName.equalsIgnoreCase(months[i])) { ... }
}
```

any month name that isn't in the list makes the loop reach i=11 and throw
ArrayIndexOutOfBoundsException.

## repro

```
A;B;a@b.c;single;1;2025-01-01T00:00;Sep 5 2025;false;
```

confirmed by compiling BookingForm.java and calling parseBooking with that
string:

```
java.lang.ArrayIndexOutOfBoundsException: Index 11 out of bounds for length 11
```

crash input is in crash_input.txt. dict.txt has month names + the separator
chars for speeding up jazzer runs.

## fix

split the merged string and use months.length:

```java
String[] months = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
for (int i = 0; i < months.length; i++) { ... }
```
