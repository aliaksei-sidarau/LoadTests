using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using BeServer;


using var rsa = RSA.Create(2048);
using var certificate = Certificate.CreateX509SelfSigned(rsa, useForServer: true);

var listener = new TcpListener(IPAddress.Loopback, 8444);
listener.Start();
Console.WriteLine("TCP server listening on 127.0.0.1:8444");

while (true)
{
    var client = await listener.AcceptTcpClientAsync();
    _ = HandleClientAsync(client, certificate);
}

async Task HandleClientAsync(TcpClient client, X509Certificate2 certificate)
{   
    using var netStream = client.GetStream();
    using var sslStream = new SslStream(netStream, false);
    try
    {
        await sslStream.AuthenticateAsServerAsync(certificate,
            clientCertificateRequired: false,
            checkCertificateRevocation: false,
            enabledSslProtocols: SslProtocols.Tls12);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"SSL handshake failed: {ex.Message}");
        client.Close();
        return;
    }

    // First message: connect
    var msg = await ReadMessageAsync(sslStream);
    if (msg == null)
    {
        client.Close();
        return;
    }

    await WriteMessageAsync(sslStream, MsgStorage.GetAuthConfirm());

    // Next: respond to each message with confirm
    while (true)
    {
        try
        {
            var nextMsg = await ReadMessageAsync(sslStream);
            if (nextMsg is null)
            {
                break;
            }
            await WriteMessageAsync(sslStream, MsgStorage.GetConfirmMsg());
        }
        catch
        {
            break;
        }
    }
    client.Close();
}

async Task<string> ReadMessageAsync(Stream stream)
{
    var lenBuf = new byte[4];
    int read = await stream.ReadAsync(lenBuf, 0, 4);
    if (read < 4)
    {
         return null;
    }

    // big-endian
    int length = (lenBuf[0] << 24) | (lenBuf[1] << 16) | (lenBuf[2] << 8) | lenBuf[3];
    var msgBuf = new byte[length];
    read = 0;

    while (read < length)
    {
        int r = await stream.ReadAsync(msgBuf, read, length - read);
        if (r == 0)
        {
            return null;
        }
        read += r;
    }
    return Encoding.UTF8.GetString(msgBuf);
}

async Task WriteMessageAsync(Stream stream, string json)
{
    var msgBuf = Encoding.UTF8.GetBytes(json);
    var lenBuf = BitConverter.GetBytes(msgBuf.Length);
    if (BitConverter.IsLittleEndian)
    {
         // convert to big-endian
        lenBuf = lenBuf.Reverse().ToArray();
    }

    await stream.WriteAsync(lenBuf, 0, 4);
    await stream.WriteAsync(msgBuf, 0, msgBuf.Length);
}
