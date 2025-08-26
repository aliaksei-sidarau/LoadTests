using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;

namespace BeServer;

public static class Certificate
{
    public const string ServerAuthenticationOid = "1.3.6.1.5.5.7.3.1";
    public const string SubjectAlternativeNameOid = "2.5.29.17";
    private const string DummyCertificateKey = "DummyCertificateKey";

    public static X509Certificate2 CreateX509SelfSigned(RSA rsa, bool useForServer = false)
    {
        // Browsers - may warn about long-lived self-signed certs (especially > 398 days).
        // macOS & iOS - may reject certificates valid for more than 1 year unless signed by a trusted CA.
        // Linux /.NET/Windows - works fine, especially for dev/test environments.
        // Industry standard   - most CAs only issue certs for max 13 months now (per Apple/Google/Mozilla policy).
        // Doesn't apply to self-signed, but good to know.
        var req = new CertificateRequest(
            "C=US,ST=SF,O=Resilio Inc.,OU=resilio,CN=localhost",
            rsa, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        if (useForServer)
        {
            req.CertificateExtensions.Add(new X509KeyUsageExtension(
                X509KeyUsageFlags.DigitalSignature | X509KeyUsageFlags.KeyEncipherment,
                critical: true));

            req.CertificateExtensions.Add(new X509EnhancedKeyUsageExtension(
                new OidCollection { new Oid(ServerAuthenticationOid) },
                critical: true));

            // Add SAN, it is now mandatory per RFC 2818 — CN is ignored by modern clients.
            var sanBuilder = new SubjectAlternativeNameBuilder();
            sanBuilder.AddDnsName("localhost");
            sanBuilder.AddIpAddress(IPAddress.Loopback);
            sanBuilder.AddIpAddress(IPAddress.IPv6Loopback);
            req.CertificateExtensions.Add(sanBuilder.Build());

            // use dummy password to avoid problems with private keys (on some platforms/implementations)
            var password = GenerateDummyPassword();
            var serverCert = req.CreateSelfSigned(DateTimeOffset.Now, DateTimeOffset.Now.AddYears(1));
            var exportedData = serverCert.Export(X509ContentType.Pfx, password);
            
            return X509CertificateLoader.LoadPkcs12(exportedData, password,
                X509KeyStorageFlags.Exportable | X509KeyStorageFlags.PersistKeySet);
        }

        var cert = req.CreateSelfSigned(DateTimeOffset.Now.AddDays(-1), DateTimeOffset.Now.AddYears(1));
        return X509CertificateLoader.LoadCertificate(cert.Export(X509ContentType.Pfx));
    }

    public static X509Certificate2 LoadX509CertificateFromPEM(string certificate)
    {
        return X509Certificate2.CreateFromPem(certificate);
    }

    public static X509Certificate2Collection LoadX509CertificatesFromPEM(string certificates)
    {
        var collection = new X509Certificate2Collection();

        collection.ImportFromPem(certificates);

        return collection;
    }
    
    private static string GenerateDummyPassword()
    {
        var result = new StringBuilder(DummyCertificateKey);
        return result.ToString();
    }
}
