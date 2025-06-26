import java.io.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.Locale;

public class BookingForm {

  public static class Booking {
  
    public final String name, surname, roomType, specialRequests;
    public final int guests;
    public final boolean freePickup;
    public final LocalDateTime arrival;
    public final LocalDate departure;

    public Booking(String name, String surname, String roomType, int guests, LocalDateTime arrival, LocalDate departure, boolean freePickup, String specialRequests) {
      this.name = name;
      this.surname = surname;
      this.roomType = roomType;
      this.guests = guests;
      this.arrival = arrival;
      this.departure = departure;
      this.freePickup = freePickup;
      this.specialRequests = specialRequests;
    }
  }


  public static String processBooking(String input) throws IOException {
  
    Booking b = parseBooking(input);
    int bookingNum = getNextBookingNumber();
    String filename = String.format("booking_%04d.txt", bookingNum);
    try (BufferedWriter writer = new BufferedWriter(new FileWriter(filename))) {
      writer.write("Name: " + b.name + "\n");
      writer.write("Surname: " + b.surname + "\n");
      writer.write("Room Type: " + b.roomType + "\n");
      writer.write("Number of Guests: " + b.guests + "\n");
      writer.write("Arrival: " + b.arrival + "\n");
      writer.write("Departure: " + b.departure + "\n");
      writer.write("Free Pickup: " + b.freePickup + "\n");
      writer.write("Special Requests: " + b.specialRequests + "\n");
    }
    return filename;
  }


  public static Booking parseBooking(String input) {
    String[] parts = input.split(";", -1);
    if (parts.length != 9) {
      throw new IllegalArgumentException("Expected 9 fields, got " + parts.length);
    }

    String name = parts[0];
    if (name.isEmpty()) {
      throw new IllegalArgumentException("Name must not be empty");
    }
    
    String surname = parts[1];
    if (surname.isEmpty()) {
      throw new IllegalArgumentException("Surname must not be empty");
    }
    
    String email = parts[2];
    if (email.isEmpty()) {
        throw new IllegalArgumentException("E-mail must not be empty");
    }
    
    String emailRegex = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$";
    Pattern EMAIL_PATTERN = Pattern.compile(emailRegex);

    if (!EMAIL_PATTERN.matcher(email).matches()) {
        throw new IllegalArgumentException("Invalid e-mail format: " + email);
    }
    
    String roomType = parts[3];
    if (!roomType.matches("single|double|suite")) {
      throw new IllegalArgumentException("Invalid room type: " + roomType);
    }

    int guests;
    try {
      guests = Integer.parseInt(parts[4]);
    } catch (NumberFormatException e) {
      throw new IllegalArgumentException("Invalid guest count", e);
    }

    LocalDateTime arrival;
    try {
      arrival = LocalDateTime.parse(parts[5],
          DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm"));
    } catch (DateTimeParseException e) {
      throw new IllegalArgumentException("Bad arrival date-time", e);
    }

    LocalDate departure;
    try{
      departure = parseDate(parts[6]);
    } catch (IllegalArgumentException e) {
        throw new IllegalArgumentException("Bad departure date: " + e.getMessage(), e);
    }
    
    if (!departure.isAfter(arrival.toLocalDate())) {
    throw new IllegalArgumentException(String.format("Departure date must be after arrival date"));
    }
    
    String freePickupTxt = parts[7].trim().toLowerCase(Locale.ROOT);
    
    boolean freePickup;
    switch (freePickupTxt) {
      case "true":
        freePickup = true;
        break;
      case "false":
        freePickup = false;
        break;
      default:
        throw new IllegalArgumentException("Invalid free pickup field" + parts[6]);
    }
    
    
    String specialRequests = parts[8];

    return new Booking(name, surname, roomType, guests, arrival, departure, freePickup, specialRequests);
  }

  private static LocalDate parseDate(String dateStr) {
  
        if (dateStr.isEmpty()) {
          throw new IllegalArgumentException("Date must not be empty");
        }
  
        Pattern iso   = Pattern.compile("^(\\d{4}) (\\d{2}) (\\d{2})$");
        Pattern text  = Pattern.compile("^([A-Za-z]+) (\\d{1,2}) (\\d{4})$");
        
        String[] months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept, Oct", "Nov", "Dec" };

        Matcher m = iso.matcher(dateStr);
        if (m.matches()) {
            int year  = Integer.parseInt(m.group(1));
            if (year < 1900 || year > 2100) {
              throw new IllegalArgumentException("Year out of supported range: " + year);
            }
            
            int month = Integer.parseInt(m.group(2));
            if (month < 1 || month > 12) {
              throw new IllegalArgumentException("Month out of supported range: " + month);
            }
            
            int day = Integer.parseInt(m.group(3));
            if (day < 1 || day > 31) {
              throw new IllegalArgumentException("Day out of supported range: " + day);
            }
            java.time.Month monthEnum = java.time.Month.of(month);
            int maxDay = monthEnum.length(java.time.Year.isLeap(year));
            if (day < 1 || day > maxDay) {
                throw new IllegalArgumentException(
                    String.format("Invalid day %d for month %s %d", day, month, year)
                );
            }
            
            return LocalDate.of(year, month, day);
        }

        m = text.matcher(dateStr);
        if (m.matches()) {
            
            String monthName = m.group(1);
            int month = -1;
            
            for (int i = 0; i < 12; i++) {
              if (monthName.equalsIgnoreCase(months[i])) {
                month = i + 1;
                break;
              }
            }
            if (month == -1) {
                throw new IllegalArgumentException("Unknown month name: " + monthName);
            }
            
            int year = Integer.parseInt(m.group(3));
            if (year < 1900 || year > 2100) {
              throw new IllegalArgumentException("Year out of supported range: " + year);
            }
            
            int day = Integer.parseInt(m.group(2));
            if (day < 1 || day > 31) {
              throw new IllegalArgumentException("Day out of supported range: " + day);
            }
            java.time.Month monthEnum = java.time.Month.of(month);
            int maxDay = monthEnum.length(java.time.Year.isLeap(year));
            if (day < 1 || day > maxDay) {
                throw new IllegalArgumentException(
                    String.format("Invalid day %d for month %s %d", day, month, year)
                );
            }

            return LocalDate.of(year, month, day);
        }
        throw new IllegalArgumentException("Unrecognized date");
    }

  private static int getNextBookingNumber() {
    File dir = new File(".");
    int max = 0;
    for (String name : dir.list()) {
      if (name.startsWith("booking_")) {
        String num = name.substring(8, name.indexOf('.'));
        try { max = Math.max(max, Integer.parseInt(num)); } catch (Exception e) {}
      }
    }
    return max + 1;
  }
}



