/**
 * 屏幕尺寸判断工具
 */
export const getScreenSize = () => {
  const width = document.body.clientWidth
  let size = -1
  if (width >= 1200) {
    size = 3 // 大屏
  } else if (width >= 992) {
    size = 2 // 中屏
  } else if (width >= 768) {
    size = 1 // 小屏
  } else {
    size = 0 // 超小屏
  }
  return size
}
