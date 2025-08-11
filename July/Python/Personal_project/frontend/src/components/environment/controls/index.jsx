import { useThree, useFrame } from "@react-three/fiber";
import { PointerLockControls } from "@react-three/drei";
import { useRef, useEffect } from "react";
import { RigidBody } from "@react-three/rapier";
import * as THREE from "three";

export default function FirstPersonCamera() {
    const { camera } = useThree();
    const keys = useRef({});
    const bodyRef = useRef(null);
    const speed = 300;

    useEffect(() => {
        const handleKeyDown = (e) => (keys.current[e.code] = true);
        const handleKeyUp = (e) => (keys.current[e.code] = false);
        window.addEventListener("keydown", handleKeyDown);
        window.addEventListener("keyup", handleKeyUp);
        return () => {
            window.removeEventListener("keydown", handleKeyDown);
            window.removeEventListener("keyup", handleKeyUp);
        };
    }, []);

    useFrame((_, delta) => {
        if (!bodyRef.current) return;

        const direction = new THREE.Vector3();
        if (keys.current["KeyW"]) direction.z -= 1;
        if (keys.current["KeyS"]) direction.z += 1;
        if (keys.current["KeyA"]) direction.x -= 1;
        if (keys.current["KeyD"]) direction.x += 1;

        direction.normalize();

        const isShift = keys.current["ShiftLeft"] || keys.current["ShiftRight"];
        const speedMultiplier = isShift ? 3 : 1;

        const currentVel = bodyRef.current.linvel();
        if (direction.length() > 0) {
            // compute horizontal move
            const moveVector = direction
                .applyQuaternion(camera.quaternion)
                .setY(0)
                .normalize()
                .multiplyScalar(speed * delta* speedMultiplier);

            // preserve vertical velocity, override horizontal
            bodyRef.current.setLinvel(
                { x: moveVector.x, y: currentVel.y, z: moveVector.z },
                true
            );
        } else {
            // no keys pressed -> stop horizontal movement immediately
            bodyRef.current.setLinvel(
                { x: 0, y: currentVel.y, z: 0 },
                true
            );
        }
        const pos = bodyRef.current.translation();
        camera.position.set(pos.x, pos.y + 1.5, pos.z);
    });

    return (
        <>
            <RigidBody
                ref={bodyRef}
                colliders="ball"
                mass={1}
                type="dynamic"
                position={[-3, 0, -3]}
                enabledRotations={[false, false, false]}
                linearDamping={1}
            />
            <PointerLockControls selector="#canvas" />
        </>
    );
}
