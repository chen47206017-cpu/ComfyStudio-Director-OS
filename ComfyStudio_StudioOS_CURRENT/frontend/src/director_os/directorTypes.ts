/**
 * Director OS 类型定义
 */


export type DirectorNodeType =

| "script"

| "canon"

| "asset"

| "reference"

| "prompt"

| "model"

| "qc"

| "delivery";



export interface DirectorNodeData{

label:string;

status?:string;

}

