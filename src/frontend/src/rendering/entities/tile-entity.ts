import { Perspective } from "rendering/perspective";
import {Textures} from "../Textures";
import {Entity} from "./entity";
import {RenderingConstants} from "../scenes/scene";
import {Position} from "models";


export enum Highlight {
    None,
    Green
}


export class TileEntity extends Entity {

    public readonly position: Position;

    public highlight = Highlight.None

    public hovered = false
    public selected = false;

    public isSpawnArea: boolean = false

    public attributes: { [key: string]: any } = {}

    constructor(instanceId: number, tileId: string, position: Position) {
        super(instanceId, tileId)

        this.position = position
    }

    render(ctx: CanvasRenderingContext2D, perspective: Perspective, constants: RenderingConstants): null {
        const {
            visible, imageStart, imageEnd, clipPoints, imageWidth, imageHeight
        } = perspective.getTileRenderingConstants(this.position, constants);

        if (!visible)
            return

        ctx.save();

        // Create Hexagon to clip the image
        ctx.beginPath();
        ctx.moveTo(clipPoints[5].x, clipPoints[5].y);
        clipPoints.forEach(({x, y}) => {
            ctx.lineTo(x, y);
        })
        ctx.closePath();
        ctx.clip();

        if (this.isSpawnArea) {
            ctx.fillStyle = "#00ff00"
            ctx.fillRect(imageStart, imageEnd, imageHeight, imageHeight)
        }

        ctx.globalAlpha = this.isSpawnArea ? 0.5 : 1
        ctx.fillStyle = this.attributes['texture.color'] ?? "#ff6699"
        ctx.fillRect(imageStart, imageEnd, imageHeight, imageHeight)

        // Render texture
        const backgroundTexture = this.attributes['texture.background']
        if (backgroundTexture) {
            const texture = Textures.get(backgroundTexture)
            ctx.drawImage(
                texture,
                0, 0,
                texture.width, texture.height,
                imageStart, imageEnd,
                imageWidth, imageHeight
            )
        }
        ctx.globalAlpha = 1

        if (this.hovered) {
            ctx.strokeStyle = "black"
            ctx.lineWidth = 5
            ctx.beginPath();
            ctx.moveTo(clipPoints[5].x, clipPoints[5].y);
            clipPoints.forEach(({x, y}) => ctx.lineTo(x, y));
            ctx.closePath();
            ctx.stroke();
        }

        if (this.selected) {
            ctx.strokeStyle = "black"
            ctx.lineWidth = 10
            ctx.beginPath();
            ctx.moveTo(clipPoints[5].x, clipPoints[5].y);
            clipPoints.forEach(({x, y}) => ctx.lineTo(x, y));
            ctx.closePath();
            ctx.stroke();
        }

        ctx.restore();

        return null
    }
}
