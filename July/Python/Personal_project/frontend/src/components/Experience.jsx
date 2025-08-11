import React, { useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment } from "@react-three/drei";
import { Physics } from "@react-three/rapier";
import { Emilian } from "./models/Emilian.jsx";
import { Andrei } from "./models/Andrei.jsx";
import { Marius } from "./models/Marius.jsx";
import { Classroom } from "./models/Classroom.jsx";
import FirstPersonCamera from "./environment/controls";
import { Vector2} from "three";

function ProximityDetector({ avatars, threshold, onProximity, active }) {
    const prev = useRef(null);
    const { camera } = useThree();
    const cam2D = useRef(new Vector2());
    const av2D = useRef(new Vector2());

    useFrame(() => {
        if (!active) {
            if (prev.current !== null) {
                prev.current = null;
                onProximity(null);
            }
            return;
        }

        cam2D.current.set(camera.position.x, camera.position.z);
        let found = null;
        for (let av of avatars) {
              av2D.current.set(av.position[0], av.position[2]);
            if (cam2D.current.distanceTo(av2D.current) < threshold) {
                    found = av.name;
                    break;
                  }
            }
        if (found !== prev.current) {
            prev.current = found;
            console.log("ProximityDetector >>> found mentor: ", found);
            onProximity(found);
        }
    });

    return null;
}

export default function Experience({ controlsEnabled = true, onProximity }) {
    // define each avatar’s world position
    const avatars = [
        { name: "Emilian", position: [-12, -7.95, -14], rotation: [0, 1, 0] },
        { name: "Andrei", position: [15, -7.95, -13], rotation: [0, 6, 0] },
        { name: "Marius", position: [-2, -7.95, 32], rotation: [0, 4.3, 0] },
    ];
    const threshold = 7; // detection radius in world units

    return (
        <Canvas id="canvas" camera={{ position: [7, 0, 13.5] }}>
            <Environment preset="sunset" />
            <ambientLight intensity={0.8} color="pink" />

            <Classroom position={[0, -8, 0]} rotation={[0, Math.PI, 0]} />

            <Emilian
                scale={[6, 6, 6]}
                position={avatars[0].position}
                rotation={avatars[0].rotation}
            />
            <Andrei
                scale={[6, 6, 6]}
                position={avatars[1].position}
                rotation={avatars[1].rotation}
            />
            <Marius
                scale={[6, 6, 6]}
                position={avatars[2].position}
                rotation={avatars[2].rotation}
            />

            <Physics gravity={[0, -9.81, 0]}>
                {controlsEnabled && <FirstPersonCamera />}
                <ProximityDetector
                    avatars={avatars}
                    threshold={threshold}
                    onProximity={onProximity}
                    active={controlsEnabled}
                />
            </Physics>
        </Canvas>
    );
}
