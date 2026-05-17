import React from 'react';

/** CRA homepage "." → Electron loadFile 下必须用相对路径 */
function assetUrl(file) {
  const base = (process.env.PUBLIC_URL || '.').replace(/\/$/, '') || '.';
  return `${base}/${file}`;
}

/** 按显示像素选最近一档 PNG，避免浏览器把大图缩糊 */
export function pickLogoSize(displayPx) {
  const tiers = [16, 24, 32, 48, 64, 96, 128, 192, 256, 512];
  const want = Math.ceil(displayPx * 2);
  for (const t of tiers) {
    if (t >= want) return t;
  }
  return 512;
}

/** 小尺寸用脑标，大尺寸用完整品牌（含 ONYX-OVERRIDE 字样） */
export function pickLogoVariant(displayPx) {
  return displayPx >= 96 ? 'full' : 'mark';
}

export default function BrandLogo({ size = 32, className = '', alt = '' }) {
  const tier = pickLogoSize(size);
  const variant = pickLogoVariant(size);
  const src = assetUrl(`logo-${tier}.png`);
  const srcSet = [16, 32, 64, 128, 256, 512]
    .map((s) => `${assetUrl(`logo-${s}.png`)} ${s}w`)
    .join(', ');

  return (
    <img
      className={className}
      src={src}
      srcSet={srcSet}
      sizes={`${size}px`}
      width={size}
      height={size}
      alt={alt}
      decoding="sync"
      draggable={false}
      data-brand-variant={variant}
    />
  );
}

export function BrandHero({ className = '', alt = '' }) {
  return (
    <img
      className={className}
      src={assetUrl('hero.png')}
      alt={alt}
      width={280}
      height={280}
      decoding="async"
      draggable={false}
    />
  );
}
