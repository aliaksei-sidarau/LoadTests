using System.ComponentModel;

namespace LoadAnalyzer;

public class PoiControl : PictureBox
{
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Visible)]
    public Point POI { get; set; }

    public PoiControl()
    {
        this.POI = Point.Empty;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);

        if (!POI.IsEmpty)
        {
            using (var pen = new Pen(Color.Yellow, 2))
            {
                // Vertical line
                e.Graphics.DrawLine(pen, POI.X, 0, POI.X, this.Height);
                // Horizontal line
                e.Graphics.DrawLine(pen, 0, POI.Y, this.Width, POI.Y);
                // Point
                e.Graphics.DrawEllipse(pen, POI.X - 2, POI.Y - 2, 4, 4);
            }
        }
    }
}