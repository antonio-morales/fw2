import java.io.StringReader;
import java.net.URLConnection;
import java.util.Random;

public class fuzzer {
    
    // Jazzer expects a public static method named fuzzerTestOneInput
    public static void fuzzerTestOneInput(byte[] data) {
    
        String s = new String(data);
        
        try {
        
          byte[] bytes = new byte[2024];
          URLConnection connection = new URLConnection("http://localhost:8080")
          connection.connect();
          new Random().nextBytes(bytes);
          connection.getOutputStream().write(bytes);

        
          throw e;
        
        } catch (Exception e) {
            // Ignore
        }
    }
}

