
using System.Globalization;
using CsvHelper;

namespace LoadAnalyzer
{
    public partial class MainForm : Form
    {
        private Button btnLoadCsv;
        private PoiControl poiControl;
        private Label lblInfo;
        private Label lblBatches;

        public MainForm()
        {
            InitializeComponent();

            // Button to load CSV
            btnLoadCsv = new Button();
            btnLoadCsv.Text = "Load CSV";
            btnLoadCsv.Location = new Point(10, 10);
            btnLoadCsv.Size = new Size(100, 30);
            btnLoadCsv.Click += btnLoadCsv_Click;
            Controls.Add(btnLoadCsv);

            // PictureBox for heatmap
            poiControl = new PoiControl();
            poiControl.Location = new Point(10, 50);
            poiControl.Size = new Size(512, 512);
            poiControl.BorderStyle = BorderStyle.FixedSingle;
            Controls.Add(poiControl);

            // Label for batches
            lblBatches = new Label();
            lblBatches.AutoSize = false;
            lblBatches.Location = new Point(poiControl.Right + 10, poiControl.Top);
            lblBatches.Size = new Size(200, 140);
            lblBatches.Text = "";
            Controls.Add(lblBatches);

            // Label for info
            lblInfo = new Label();
            lblInfo.Location = new Point(120, 15);
            lblInfo.Size = new Size(300, 20);
            lblInfo.Text = "Select a CSV file with 3 columns: X, Y, Value";
            Controls.Add(lblInfo);


            // Info for showing POI values
            poiControl.MouseClick += (s, e) =>
            {
                poiControl.POI = new Point(e.X, e.Y);
                poiControl.Invalidate();

                if (poiControl.Image is Bitmap bmp)
                {
                    if (e.X >= 0 && e.X < bmp.Width && e.Y >= 0 && e.Y < bmp.Height)
                    {
                        var values = $"{_valueMatrix[e.X, e.Y]}".Split(
                            ',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);
                        lblBatches.Text = string.Join(",\n", values);
                    }
                }
            };
        }

        private void btnLoadCsv_Click(object sender, EventArgs e)
        {
            var ofd = new OpenFileDialog();
            ofd.Filter = "CSV files (*.csv)|*.csv";
            if (ofd.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    var records = LoadCsv(ofd.FileName);
                    var bmp = BuildHeatmap(records);
                    poiControl.Image = bmp;
                    lblInfo.Text = $"Loaded {records.Count} points.";
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error loading CSV: {ex.Message}");
                }
            }
        }

        private List<CsvEntry> LoadCsv(string path)
        {
            using var reader = new StreamReader(path);
            using var csv = new CsvReader(reader, CultureInfo.InvariantCulture);
            var data = csv.GetRecords<CsvEntry>().ToList();
            
            return data;
        }

        private static CsvEntry[,] _valueMatrix = new CsvEntry[0, 0];

        private Bitmap BuildHeatmap(List<CsvEntry> data)
        {
            var agents = data.Select(x => x.AgentsCount).Distinct().OrderBy(x => x).ToList();
            var batches = data.Select(x => x.BatchSize).Distinct().OrderBy(x => x).ToList();
            var matrix = new CsvEntry[agents.Count, batches.Count];
            for (int i = 0; i < agents.Count; i++)
            {
                for (int j = 0; j < batches.Count; j++)
                {
                    var entry = data.FirstOrDefault(x => x.AgentsCount == agents[i] && x.BatchSize == batches[j]);
                    matrix[i, j] = entry ?? new CsvEntry { AgentsCount = agents[i], BatchSize = batches[j], BestConfirmedEsp = 0 };
                }
            }

            var minEps = data.Min(x => x.BestConfirmedEsp);
            var maxEps = data.Max(x => x.BestConfirmedEsp);
            double epsRange = maxEps - minEps;
            if (epsRange == 0) epsRange = 1; // Prevent division by zero

            int width = poiControl.Width;
            int height = poiControl.Height;
            var bmp = new Bitmap(width, height);
            _valueMatrix = new CsvEntry[width, height];

            for (var x = 0; x < width; x++)
            {
                for (var y = 0; y < height; y++)
                {
                    // Map each pixel to the nearest grid cell
                    int gridX = x * agents.Count / width;
                    int gridY = y * batches.Count / height;
                    gridX = Math.Min(gridX, agents.Count - 1);
                    gridY = Math.Min(gridY, batches.Count - 1);
                    var entry = matrix[gridX, gridY];
                    _valueMatrix[x, y] = entry;

                    var intensity = (int)((entry.BestConfirmedEsp - minEps) / epsRange * 255);
                    Color color = Color.FromArgb(255, intensity, 0, 255 - intensity); // purple to blue
                    bmp.SetPixel(x, y, color);
                }
            }

            // Draw values
            using (Graphics g = Graphics.FromImage(bmp))
            {
                var font = new Font("Arial", 10);
                var brush = Brushes.White;

                // Draw first point batch\agent
                g.DrawString($"{batches[0]}\\{agents[0]}", font, brush, 0, 2);

                // Draw agent labels along X axis
                for (int i = 1; i < agents.Count; i++)
                {
                    float x = i * bmp.Width / (float)agents.Count;
                    g.DrawString(agents[i].ToString(), font, brush, x, 2);
                }

                // Draw batch labels along Y axis
                for (int j = 1; j < batches.Count; j++)
                {
                    float y = j * bmp.Height / (float)batches.Count;
                    g.DrawString(batches[j].ToString(), font, brush, 2, y);
                }
            }
            return bmp;
        }
    }
}
