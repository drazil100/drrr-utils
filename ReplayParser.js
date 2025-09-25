const fs = typeof require == 'undefined' ? null : require('node:fs');
const process = typeof require == 'undefined' ? null : require('node:process');

class DriveReader {
  constructor(url) {
    if (fs) {
      this.data = fs.readFileSync(url).toString('binary');
    } else {
      const fileId = getIdFromUrl(url);                         // Extract file ID from the Drive link
      const file = DriveApp.getFileById(fileId);                // Get the file object using the file ID
      const content = file.getBlob().getBytes();                // Fetch the uploaded file content
      this.data = Utilities.newBlob(content).getDataAsString('ISO-8859-1'); // Convert bytes to string
    }
    this.cursor = 0;
  }

  skip(count) {
    this.cursor += count;
  }

  seek(pos) {
    this.cursor = pos;
  }

  readByte() {
    if (this.cursor >= this.data.length) {
      throw new Error('read out of bounds');
    }
    return this.data.charCodeAt(this.cursor++) & 0xFF;
  }

  readBytes(len) {
    if (this.cursor + len > this.data.length) {
      throw new Error('read out of bounds');
    }
    const start = this.cursor;
    this.cursor += len;
    return this.data.substring(start, this.cursor);
  }

  readInt(len) {
    let val = 0;
    for (let i = 0; i < len; i++) {
      val = val | (this.readByte() << (8 * i));
    }
    return val;
  }

  readIntBE(len) {
    let val = 0;
    for (let i = 0; i < len; i++) {
      val = (val << 8) | this.readByte();
    }
    return val;
  }

  readUIntBE(len) {
    const val = this.readIntBE(len);
    if (val < 0) {
      return -1 - val;
    }
    return val;
  }

  readString() {
    const start = this.cursor;
    const end = this.data.indexOf('\0', start);
    if (end < start) {
      throw new Error('delimiter not found');
    }
    this.cursor = end + 1;
    return this.data.substring(start, end);
  }

  find(str) {
    const pos = this.data.indexOf(str, this.cursor);
    if (pos < this.cursor) {
      throw new Error('match not found');
    }
    this.cursor = pos;
  }

  readUBJString() {
    const length = this.readUBJValue();
    const str = this.data.substring(this.cursor, this.cursor + length);
    this.cursor += length;
    return str;
  }

  readUBJContainerParams() {
    const meta = {
      type: null,
      count: null,
    };
    let type = this.data[this.cursor];
    if (type == '$') {
      this.skip(1);
      meta.type = this.readByte();
      type = this.data[this.cursor];
    }
    if (type == '#') {
      this.skip(1);
      meta.count = this.readUBJValue();
    }
    return meta;
  }

  readUBJArray() {
    const obj = [];
    const meta = this.readUBJContainerParams();
    if (meta.count !== null) {
      while (meta.count > 0) {
        const val = this.readUBJValue(meta.type);
        obj.push(val);
        --meta.count;
      }
    } else {
      while (this.data[this.cursor] != ']') {
        const val = this.readUBJValue();
        obj.push(val);
      }
      // throw away ]
      this.readByte();
    }
    return obj;
  }

  readUBJObject() {
    const obj = {};
    const meta = this.readUBJContainerParams();
    if (meta.count !== null) {
      while (meta.count > 0) {
        const key = this.readUBJString();
        const val = this.readUBJValue(meta.type);
        obj[key] = val;
        --meta.count;
      }
    } else {
      while (this.data[this.cursor] != '}') {
        const key = this.readUBJString();
        const val = this.readUBJValue();
        obj[key] = val;
      }
      // throw away closing brace
      this.readByte();
    }
    return obj;
  }

  readUBJValue(type = null) {
    if (type === null) {
      type = String.fromCharCode(this.readByte());
    }
    switch (type) {
      case 'i': // Int8
        return this.readIntBE(1);
      case 'U': // Uint8
        return this.readUIntBE(1);
      case 'I': // Int16
        return this.readIntBE(2);
      case 'l': // Int32
        return this.readIntBE(4);
      case 'L': // Int64
        return this.readIntBE(8);
      case 'd': // Float32
        return this.readFloat(4, 'getFloat32');
      case 'D': // Float64
        return this.readFloat(8, 'getFloat64');
      case 'S': // String
        return this.readUBJString();
      case '[': // Start of array
        return this.readUBJArray();
      case '{': // Start of object
        return this.readUBJObject();
      case 'Z': // Null
        return null;
      case 'T': // True
        return true;
      case 'F': // False
        return false;
      default:
        throw new Error(`Invalid UBJSON type: ${type.charCodeAt(0)} at position ${this.cursor}`);
    }
  }

  readFloat(len, getter) {
    let view = new DataView(new ArrayBuffer(len));
    for (let i = 0; i < len; i++) {
      view.setUint8(i, this.readByte());
    }
    return view[getter](0);
  }
}

function parseReplay(url) {
  const reader = new DriveReader(url);

  reader.seek(0x0C);
  const version = reader.readByte() + "." + reader.readByte();

  const ghostVersion = reader.readInt(2);
  const replayTitle = reader.readString();

  reader.seek(0x64);
  const map = reader.readString();
  const md5 = reader.readBytes(16);

  const demoFlags1 = reader.readByte();
  const demoFlags2 = reader.readByte();
  const noNetMultiplayer = Boolean(demoFlags1 & 0x10);
  const multiplayer = Boolean(demoFlags1 & 0x80);
  const grandPrix = Boolean(demoFlags2 & 0x01);
  const spbAttack = Boolean(demoFlags1 & 0x4);
  const encore = Boolean(demoFlags1 & 0x40);

  const replayType = reader.readString();
  const laps = reader.readByte();

  const addons = reader.readByte();
  const addonFiles = [];
  for (let i = 0; i < addons; i++) {
    const filename = reader.readString();
    const md5 = reader.readBytes(16);
    addonFiles.push(filename);
  }

  let numSkins;
  if (ghostVersion >= 0x000E) {
    numSkins = reader.readInt(2);
  } else {
    numSkins = reader.readByte();
  }
  const skinList = [];
  for (let i = 0; i < numSkins; i++) {
    const pos = reader.cursor;
    const skin = reader.readString();
    reader.seek(pos + 16);
    const speed = reader.readByte();
    const weight = reader.readByte();
    reader.seek(pos + 22);
    skinList.push({
      skin,
      speed,
      weight,
    });
  }

  reader.find("standings[");
  reader.skip(9);
  const standingsData = reader.readUBJValue();

  const standings = standingsData.map((standing) => {
    const result = {
      name: standing.name,
      ranking: standing.ranking,
      skincolor: standing.skincolor,
      ...skinList[standing.demoskin],
    };

    result.time = getTime(standing.timeorscore);
    return result;
  });

  return {
    version,
    title: replayTitle.replace(/[^ -~]/g, ''),
    addons: addonFiles,
    map,
    md5: toHex(md5),
    laps,
    replayType,
    spbAttack,
    encore,
    isOfflineMultiplayer: noNetMultiplayer,
    isOnlineMultiplayer: multiplayer,
    isGrandPrix: grandPrix,
    standings,
  };
}

function getTime(frames) {
  if (frames < 0) return "DNF"
  let seconds = (parseInt(frames)/35)+0.00001;
  const minutes = Math.floor(seconds / 60);
  seconds = seconds - minutes*60;
  let centiseconds = Math.floor((seconds - Math.floor(seconds))*100);
  seconds = Math.floor(seconds);

  if (seconds < 10) seconds = "0" + seconds;
  if (centiseconds < 10) centiseconds = "0" + centiseconds;

  return `${minutes}' ${seconds}" ${centiseconds}`;
}

function getIdFromUrl(url) {
  const match = url.match(/[-\w]{25,}/);
  if (match) {
    return match[0];
  } else {
    throw new Error('Invalid Google Drive URL');
  }
}

function toHex(str) {
  return Array.from(str).map((ch) => `0${ch.charCodeAt(0).toString(16)}`.slice(-2)).join('');
}

if (process && process.argv[2]) {
  console.log(parseReplay(process.argv[2]));
}
