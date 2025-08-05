// src/utils/indexeddb-utils.ts

const DB_NAME = 'CryptoVoteDB';
const DB_VERSION = 2;

function openDB(storeName: string): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: 'id' });
      }
    };

    request.onsuccess = () => {
      const db = request.result;
      // Ensure the store exists even if version upgrade didn't trigger
      if (!db.objectStoreNames.contains(storeName)) {
        db.close();
        const upgradeRequest = indexedDB.open(DB_NAME, DB_VERSION + 1);
        upgradeRequest.onupgradeneeded = (event) => {
          const db2 = (event.target as IDBOpenDBRequest).result;
          db2.createObjectStore(storeName, { keyPath: 'id' });
        };
        upgradeRequest.onsuccess = () => resolve(upgradeRequest.result);
        upgradeRequest.onerror = () => reject(upgradeRequest.error);
      } else {
        resolve(db);
      }
    };

    request.onerror = () => reject(request.error);
  });
}

export async function saveToIndexedDB(storeName: string, value: any): Promise<void> {
  const db = await openDB(storeName);
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    tx.objectStore(storeName).put(value);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

export async function getFromIndexedDB(storeName: string, key: string): Promise<any> {
  const db = await openDB(storeName);
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const getRequest = store.get(key);

    getRequest.onsuccess = () => {
      db.close();
      resolve(getRequest.result);
    };
    getRequest.onerror = () => {
      db.close();
      reject(getRequest.error);
    };
  });
}
