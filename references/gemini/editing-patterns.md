# Editing patterns

## 1. Direct modification

Use one input image and say exactly what changes.

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/nanobanana.sh \
  -i input.png -o output.png \
  "replace the background with a rainy Tokyo street at night, keep the subject, pose, and framing unchanged"
```

Best for:
- background swaps
- clothing/color tweaks
- adding or removing accessories
- mild retouching

## 2. Style transfer

Use one content image and one style reference.

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/nanobanana.sh \
  -i content.png -i style.png -o stylized.png \
  "apply the visual style of the second image to the first, preserve the first image's composition"
```

Best for:
- watercolor / anime / illustration conversions
- branded style consistency
- poster-like transformations

## 3. Scene composition

Use multiple inputs and define each image's role.

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/nanobanana.sh \
  -i room.png -i chair.png -i lamp.png -o composed.png \
  "place the chair and lamp naturally into the room, match shadows, perspective, and color temperature"
```

Best for:
- mockups
- product-in-room placement
- combining separate subjects into one scene

## 4. Template-first workflow

Create a template once, then reuse it for a batch.

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/nanobanana.sh \
  -aspect 16:9 -size 2K -o template.png \
  "clean presentation slide template, dark blue gradient, elegant glowing separators"
```

Then:

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/nanobanana.sh \
  -i template.png -aspect 16:9 -size 2K -o slide-02.png \
  "using this same style, create a slide showing three product benefits"
```

## Editing prompt formula

Use this pattern when you need tighter control:

- **Keep**: what must stay unchanged
- **Change**: what should be edited
- **Style**: how the result should look
- **Quality**: lighting, realism, composition, cleanliness

Example:

> Keep the person, pose, and camera framing unchanged. Change the background to a clean futuristic lab. Style: photorealistic with soft cinematic lighting. Maintain natural shadows and realistic reflections.
