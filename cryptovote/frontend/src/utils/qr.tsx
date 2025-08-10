export async function toDataUrl(text: string): Promise<string | null> {
    try {
      const { default: QRCode } = await import('qrcode');
      return await QRCode.toDataURL(text);
    } catch {
      return null;
    }
  }