import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class SNTPClient {
    private static final int SIZE_OF_PACKET = 48;
    private static final int REFERENCE_TIME_OFFSET = 16;
    private static final int ORIGINATE_TIME_OFFSET = 24;
    private static final int RECEIVE_TIME_OFFSET = 32;
    private static final int TRANSMIT_TIME_OFFSET = 40;
    private static final int PORT = 123;
    private static final int CLIENT_MODE_CODE = 3;
    private static final int PROTOCOL_VERSION = 3;
    private static final long SYSTEM_TO_NTP_TIME_DELTA = ((365L * 70L) + 17L) * 24L * 60L * 60L;

    // system time computed from NTP server response
    private long mNtpTime;
    // last time from watches on server
    private long mReferenceTime;


    // requests time from server and receives answer
    public boolean request(String serverAddress, int timeout) {
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.setSoTimeout(timeout);
            InetAddress address = InetAddress.getByName(serverAddress);
            byte[] buffer = new byte[SIZE_OF_PACKET];
            DatagramPacket request = new DatagramPacket(buffer, buffer.length, address, PORT);

            buffer[0] = CLIENT_MODE_CODE | (PROTOCOL_VERSION << 3);

            long requestTime = System.currentTimeMillis();
            // report time of requesting from client
            writeTime(buffer, TRANSMIT_TIME_OFFSET, requestTime);
            socket.send(request);

            // read the response
            DatagramPacket response = new DatagramPacket(buffer, buffer.length);
            socket.receive(response);

            // when client received
            long arriveTime = System.currentTimeMillis();

            // when client transmitted
            long originateTime = readTime(buffer, ORIGINATE_TIME_OFFSET);
            // when server received
            long receiveTime = readTime(buffer, RECEIVE_TIME_OFFSET);
            // when server transmitted
            long transmitTime = readTime(buffer, TRANSMIT_TIME_OFFSET);
            // last asked phys clock time from server
            long referenceTime = readTime(buffer, REFERENCE_TIME_OFFSET);


            long timeForTravel = (arriveTime - originateTime - (transmitTime - receiveTime)) / 2;
            long clockOffset = receiveTime - (originateTime + timeForTravel);

            mNtpTime = arriveTime + clockOffset;
            mReferenceTime = referenceTime;
        } catch (Exception e) {
            return false;
        }
        return true;
    }

    public long getTime() {
        return mNtpTime;
    }

    public long getReferenceTime() {
        return mReferenceTime;
    }

    private long read32(byte[] buffer, int offset) {
        byte b0 = buffer[offset];
        byte b1 = buffer[offset + 1];
        byte b2 = buffer[offset + 2];
        byte b3 = buffer[offset + 3];

        // convert signed bytes to unsigned values
        int i0 = ((b0 & 0x80) == 0x80 ? (b0 & 0x7F) + 0x80 : b0);
        int i1 = ((b1 & 0x80) == 0x80 ? (b1 & 0x7F) + 0x80 : b1);
        int i2 = ((b2 & 0x80) == 0x80 ? (b2 & 0x7F) + 0x80 : b2);
        int i3 = ((b3 & 0x80) == 0x80 ? (b3 & 0x7F) + 0x80 : b3);

        return ((long) i0 << 24) + ((long) i1 << 16) + ((long) i2 << 8) + (long) i3;
    }

    private long readTime(byte[] buffer, int offset) {
        long seconds = read32(buffer, offset);
        long fraction = read32(buffer, offset + 4);
        return (seconds - SYSTEM_TO_NTP_TIME_DELTA) * 1000 + (fraction * 1000L) / 0x100000000L;
    }

    private void writeTime(byte[] buffer, int offset, long time) {
        long seconds = time / 1000L;
        long milliseconds = time - seconds * 1000L;
        seconds += SYSTEM_TO_NTP_TIME_DELTA;

        buffer[offset++] = (byte) (seconds >> 24);
        buffer[offset++] = (byte) (seconds >> 16);
        buffer[offset++] = (byte) (seconds >> 8);
        buffer[offset++] = (byte) seconds;

        long fraction = milliseconds * 0x100000000L / 1000L;
        buffer[offset++] = (byte) (fraction >> 24);
        buffer[offset++] = (byte) (fraction >> 16);
        buffer[offset++] = (byte) (fraction >> 8);
        // low order bits should be random data
        buffer[offset] = (byte) (Math.random() * 255.0);
    }
}
