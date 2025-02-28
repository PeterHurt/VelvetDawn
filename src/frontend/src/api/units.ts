import {get, post} from "./utils";
import {AvailableUnitUpgradesAndAbilities, GameState, Position} from "models";
import {VelvetDawn} from "velvet-dawn/velvet-dawn";


export function move(entityPk: string, path: Position[]): Promise<GameState> {
    return post("/units/move/", {
        username: VelvetDawn.loginDetails.username,
        password: VelvetDawn.loginDetails.password,
        "entity": entityPk,
        "path": JSON.stringify(path)
    })
}

export function getAvailableUpgradeAndAbilities(entityPk: string): Promise<AvailableUnitUpgradesAndAbilities> {
    return get(`/units/available-upgrades-and-abilities/?username=${VelvetDawn.loginDetails.username}&password=${VelvetDawn.loginDetails.password}&id=${entityPk}`)
}


export function performUpgrade(entityPk: string, upgradeId: string): Promise<AvailableUnitUpgradesAndAbilities> {
    return post("/units/upgrade/", {
        username: VelvetDawn.loginDetails.username,
        password: VelvetDawn.loginDetails.password,
        id: entityPk,
        upgrade: upgradeId
    })
}


export function performAbility(entityPk: string, abilityId: string): Promise<AvailableUnitUpgradesAndAbilities> {
    return post("/units/ability/", {
        username: VelvetDawn.loginDetails.username,
        password: VelvetDawn.loginDetails.password,
        id: entityPk,
        ability: abilityId
    })
}
