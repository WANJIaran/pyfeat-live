// Native browser-side camera enumeration + getUserMedia, with proper
// {exact: id} constraints so device picks are honoured.

export interface CameraDevice {
  deviceId: string;
  label: string;
}

export const cameraStore = $state<{
  devices: CameraDevice[];
  selectedDeviceId: string | null;
  stream: MediaStream | null;
  error: string | null;
}>({
  devices: [],
  selectedDeviceId: null,
  stream: null,
  error: null,
});

function friendlyCameraError(err: unknown): string {
  const name = err instanceof DOMException ? err.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError') {
    return '摄像头权限被拒绝。请在 Windows“设置 → 隐私和安全性 → 相机”中允许桌面应用访问摄像头，然后重新打开本软件。';
  }
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
    return '没有检测到摄像头，请检查摄像头是否连接并已启用。';
  }
  if (name === 'NotReadableError' || name === 'TrackStartError') {
    return '摄像头无法读取，可能正被微信、会议软件或浏览器占用。请关闭其他使用摄像头的程序后重试。';
  }
  if (name === 'OverconstrainedError' || name === 'ConstraintNotSatisfiedError') {
    return '摄像头不支持所请求的画面参数，请换一个摄像头重试。';
  }
  const detail = err instanceof Error ? err.message : String(err ?? '未知错误');
  return `摄像头错误：${detail}`;
}

export async function refreshDevices(): Promise<void> {
  cameraStore.error = null;
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraStore.error = '当前系统不支持摄像头访问，请确认已安装 Microsoft Edge WebView2 Runtime。';
    cameraStore.devices = [];
    cameraStore.selectedDeviceId = null;
    return;
  }
  try {
    // Trigger a permission request if we don't have one — without it,
    // enumerateDevices returns blank labels.
    try {
      const permissionStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      permissionStream.getTracks().forEach(t => t.stop());
    } catch (err) {
      cameraStore.error = friendlyCameraError(err);
    }

    const all = await navigator.mediaDevices.enumerateDevices();
    cameraStore.devices = all
      .filter(d => d.kind === 'videoinput')
      .map(d => ({
        deviceId: d.deviceId,
        label: d.label || `摄像头 ${d.deviceId.slice(0, 6)}`,
      }));
    if (!cameraStore.selectedDeviceId && cameraStore.devices.length > 0) {
      cameraStore.selectedDeviceId = cameraStore.devices[0].deviceId;
    }
  } catch (err) {
    // A thrown non-Error (string, DOMException without .message, null) would
    // otherwise store `undefined` or throw inside the catch.
    cameraStore.error = friendlyCameraError(err);
  }
}

export async function startCamera(
  deviceId: string, width: number, height: number,
): Promise<MediaStream> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error('当前系统不支持摄像头访问');
  }
  if (cameraStore.stream) {
    cameraStore.stream.getTracks().forEach(t => t.stop());
  }
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: { exact: deviceId },
        width: { ideal: width },
        height: { ideal: height },
        frameRate: { ideal: 30 },
      },
      audio: false,
    });
  } catch (err) {
    cameraStore.error = friendlyCameraError(err);
    throw new Error(cameraStore.error);
  }
  cameraStore.stream = stream;
  cameraStore.selectedDeviceId = deviceId;
  cameraStore.error = null;
  return stream;
}

export function stopCamera(): void {
  if (cameraStore.stream) {
    cameraStore.stream.getTracks().forEach(t => t.stop());
    cameraStore.stream = null;
  }
}
