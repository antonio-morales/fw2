//DEPS com.squareup.okhttp3:okhttp:4.9.3
//JAVA 17

import okhttp3.*;
import java.util.Random;

public class HttpClientRandomData {
    public static void main(String[] args) throws Exception {
        String url = "http://localhost:80";
        int dataLength = args.length > 0 ? Integer.parseInt(args[0]) : 128;

        byte[] randomData = new byte[dataLength];
        new Random().nextBytes(randomData);

        OkHttpClient client = new OkHttpClient();

        RequestBody body = RequestBody.create(randomData, MediaType.parse("application/octet-stream"));
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        try (Response response = client.newCall(request).execute()) {
            System.out.println("Response: " + response.code());
            System.out.println("Body: " + response.body().string());
        }
    }
}