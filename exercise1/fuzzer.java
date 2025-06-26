import java.io.StringReader;

public class fuzzer {
    
    // Jazzer expects a public static method named fuzzerTestOneInput
    public static void fuzzerTestOneInput(byte[] data) {
    
        String s = new String(data);
        
        try {
        
          BookingForm.parseBooking(s);
          
        } catch (ArrayIndexOutOfBoundsException e) {
        
          throw e;
        
        } catch (Exception e) {
            // Ignore
        }
    }
}

