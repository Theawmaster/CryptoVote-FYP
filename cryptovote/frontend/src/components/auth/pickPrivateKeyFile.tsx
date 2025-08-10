export function pickPrivateKeyFile(): Promise<string> {
    return new Promise<string>((resolve, reject) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.pem';
      input.onchange = async () => {
        try {
          const file = input.files?.[0];
          if (!file) return reject('No file selected');
          const pem = await file.text();
          resolve(pem);
        } catch (e: any) {
          reject(e?.message || 'Failed to read file');
        } finally {
          input.value = '';
        }
      };
      input.click();
    });
  }
  