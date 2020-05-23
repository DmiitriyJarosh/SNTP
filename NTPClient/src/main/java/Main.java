import java.util.Date;

public class Main {

    private static final String NTP_SERVER_ADDRESS = "ntp1.stratum2.ru";
    private static final String NTP_SERVER_ADDRESS_MY = "127.0.0.1";

    public static void main(String[] args) {
        SNTPClient sntpClient = new SNTPClient();

        if (sntpClient.request(NTP_SERVER_ADDRESS, 3000)) {
            Date curData = new Date(sntpClient.getTime());
            Date lastClockData = new Date(sntpClient.getReferenceTime());
            System.out.println("Current time by calculations: " + curData.toString());
            System.out.println("Time which server sent as clock time: " + lastClockData.toString());
        }
    }
}
