import { useState, useRef, useEffect } from 'react';
import { FiTrash2, FiDownload, FiUpload } from 'react-icons/fi';

interface ImageItem {
  id: string;
  src: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface MoodboardData {
  images: ImageItem[];
  canvasData?: string;
}

interface Props {
  content: string;
  onChange: (data: string) => void;
}

export default function MoodboardEditor({ content, onChange }: Props) {
  const [data, setData] = useState<MoodboardData>(() => {
    try {
      return content ? JSON.parse(content) : { images: [] };
    } catch {
      return { images: [] };
    }
  });

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [draggedImage, setDraggedImage] = useState<ImageItem | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Persist to parent on change
  const saveData = (newData: MoodboardData) => {
    setData(newData);
    onChange(JSON.stringify(newData));
  };

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear and redraw
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    // Draw images
    data.images.forEach((img) => {
      const image = new Image();
      image.onload = () => {
        ctx.drawImage(image, img.x, img.y, img.width, img.height);
      };
      image.src = img.src;
    });

    // Load saved canvas drawing if exists
    if (data.canvasData) {
      const savedImage = new Image();
      savedImage.onload = () => {
        ctx.drawImage(savedImage, 0, 0);
      };
      savedImage.src = data.canvasData;
    }
  }, [data]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const src = event.target?.result as string;
        const newImage: ImageItem = {
          id: `img-${Date.now()}-${Math.random()}`,
          src,
          x: 50,
          y: 50,
          width: 150,
          height: 150,
        };
        saveData({ ...data, images: [...data.images, newImage] });
      };
      reader.readAsDataURL(file);
    });

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if clicking on an image
    const clicked = [...data.images].reverse().find((img) => {
      return x >= img.x && x <= img.x + img.width && y >= img.y && y <= img.y + img.height;
    });

    if (clicked) {
      setDraggedImage(clicked);
    } else {
      setIsDrawing(true);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (draggedImage) {
      const newImages = data.images.map((img) =>
        img.id === draggedImage.id ? { ...img, x, y } : img
      );
      setData({ ...data, images: newImages });
      setDraggedImage({ ...draggedImage, x, y });
    } else if (isDrawing) {
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 2;
      ctx.lineTo(x, y);
      ctx.stroke();
    }
  };

  const handleCanvasMouseUp = () => {
    if (draggedImage) {
      // Update the data with new position
      const newImages = data.images.map((img) =>
        img.id === draggedImage.id ? draggedImage : img
      );
      saveData({ ...data, images: newImages });
      setDraggedImage(null);
    } else if (isDrawing) {
      setIsDrawing(false);
      // Save canvas drawing
      if (canvasRef.current) {
        saveData({ ...data, canvasData: canvasRef.current.toDataURL() });
      }
    }
  };

  const removeImage = (id: string) => {
    saveData({ ...data, images: data.images.filter((img) => img.id !== id) });
  };

  const clearCanvas = () => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        saveData({ ...data, canvasData: undefined });
      }
    }
  };

  const downloadImage = () => {
    if (!canvasRef.current) return;
    const link = document.createElement('a');
    link.href = canvasRef.current.toDataURL('image/png');
    link.download = `moodboard-${Date.now()}.png`;
    link.click();
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-gray-50">
      {/* Toolbar */}
      <div className="flex-shrink-0 flex items-center gap-2 px-4 py-3 bg-white border-b border-gray-200 flex-wrap">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <FiUpload className="w-4 h-4" />
          Add Image
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleImageUpload}
          className="hidden"
        />

        <button
          onClick={clearCanvas}
          className="flex items-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
        >
          <FiTrash2 className="w-4 h-4" />
          Clear Drawing
        </button>

        <button
          onClick={downloadImage}
          className="flex items-center gap-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors ml-auto"
        >
          <FiDownload className="w-4 h-4" />
          Download
        </button>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-4">
        <canvas
          ref={canvasRef}
          width={1000}
          height={800}
          onMouseDown={handleCanvasMouseDown}
          onMouseMove={handleCanvasMouseMove}
          onMouseUp={handleCanvasMouseUp}
          onMouseLeave={handleCanvasMouseUp}
          className="bg-white border-2 border-gray-300 rounded-lg shadow-lg cursor-crosshair"
          style={{ maxWidth: '100%', height: 'auto' }}
        />
      </div>

      {/* Images List Sidebar */}
      {data.images.length > 0 && (
        <div className="flex-shrink-0 w-full max-h-24 overflow-y-auto bg-white border-t border-gray-200 px-4 py-3">
          <p className="text-xs font-semibold text-gray-600 mb-2">Images ({data.images.length})</p>
          <div className="flex gap-2 flex-wrap">
            {data.images.map((img) => (
              <div
                key={img.id}
                className="relative group"
              >
                <img
                  src={img.src}
                  alt="moodboard item"
                  className="h-16 w-16 object-cover rounded border border-gray-200"
                />
                <button
                  onClick={() => removeImage(img.id)}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <FiTrash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
