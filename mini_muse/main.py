"""Main entry point for mini_muse application."""

import sys
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from PIL import Image

from mini_muse.config import load_config, AppConfig
from mini_muse.services.upscaling import create_upscaling_service
from mini_muse.services.video_generation import create_video_pipeline
from mini_muse.services.image_generation import create_image_generation_service
from mini_muse.services.prompt_enhancement import create_prompt_enhancer
from mini_muse import __version__

app = typer.Typer(
    name="mini-muse",
    help="AI-powered image generation and feedback application",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
) -> None:
    """Run the mini_muse TUI application."""
    try:
        # Load configuration
        config = load_config(config_file)
        
        if debug:
            config.log_level = "DEBUG"
            console.print("[yellow]Debug mode enabled[/yellow]")
        
        # Display startup information
        console.print(
            Panel(
                f"[bold blue]mini_muse v{__version__}[/bold blue]\n"
                f"AI-powered image generation and feedback application\n\n"
                f"Configuration: {config_file or 'default'}\n"
                f"Log level: {config.log_level}",
                title="Starting mini_muse",
                border_style="blue",
            )
        )
        
        # TODO: Initialize and run TUI application
        console.print("[yellow]TUI application initialization will be implemented in future tasks[/yellow]")
        console.print("[green]Configuration loaded successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Error starting application: {e}[/red]")
        sys.exit(1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        "-r",
        help="Reset configuration to defaults",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Manage application configuration."""
    try:
        if reset:
            from mini_muse.config import Config
            config_manager = Config(config_file)
            config_manager.reset_to_defaults()
            console.print("[green]Configuration reset to defaults[/green]")
            return
        
        if show:
            config = load_config(config_file)
            console.print(
                Panel(
                    config.json(indent=2),
                    title="Current Configuration",
                    border_style="green",
                )
            )
        else:
            console.print("Use --show to display configuration or --reset to reset to defaults")
            
    except Exception as e:
        console.print(f"[red]Error managing configuration: {e}[/red]")
        sys.exit(1)


@app.command()
def upscale(
    input_path: Path = typer.Argument(
        ...,
        help="Path to input image file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for upscaled image (optional)",
    ),
    scale_factor: int = typer.Option(
        4,
        "--scale",
        "-s",
        min=2,
        max=4,
        help="Upscaling factor (2 or 4)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Upscaling model to use (realesrgan-x2plus, realesrgan-x4plus, realesrgan-x4plus-anime)",
    ),
    face_enhance: bool = typer.Option(
        False,
        "--face-enhance",
        "-f",
        help="Apply face enhancement using GFPGAN",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """Upscale an image using Real-ESRGAN."""
    async def _upscale():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create upscaling service
            upscaling_service = create_upscaling_service(config)
            if upscaling_service is None:
                console.print("[red]Upscaling service not available. Please install dependencies:[/red]")
                console.print("pip install basicsr realesrgan gfpgan")
                sys.exit(1)
            
            # Load input image
            console.print(f"[blue]Loading image: {input_path}[/blue]")
            image = Image.open(input_path)
            
            # Determine output path
            if output_path is None:
                stem = input_path.stem
                suffix = input_path.suffix
                output_path = input_path.parent / f"{stem}_upscaled_{scale_factor}x{suffix}"
            
            console.print(f"[blue]Input size: {image.size}[/blue]")
            estimated_size = upscaling_service.estimate_output_size(image.size, scale_factor)
            estimated_memory = upscaling_service.estimate_memory_usage(image.size, scale_factor)
            console.print(f"[blue]Estimated output size: {estimated_size}[/blue]")
            console.print(f"[blue]Estimated memory usage: {estimated_memory:.1f} MB[/blue]")
            
            # Check memory usage
            if estimated_memory > config.upscaling.max_memory_usage_mb:
                console.print(f"[yellow]Warning: Estimated memory usage ({estimated_memory:.1f} MB) exceeds configured limit ({config.upscaling.max_memory_usage_mb} MB)[/yellow]")
                if not typer.confirm("Continue anyway?"):
                    console.print("[yellow]Upscaling cancelled[/yellow]")
                    return
            
            # Perform upscaling with progress display
            with Progress() as progress:
                task = progress.add_task("Upscaling image...", total=100)
                
                # Update progress (simplified for demo)
                progress.update(task, advance=20)
                console.print("[blue]Loading model...[/blue]")
                
                progress.update(task, advance=30)
                console.print("[blue]Processing image...[/blue]")
                
                # Actual upscaling
                upscaled_image = await upscaling_service.upscale_image(
                    image=image,
                    scale_factor=scale_factor,
                    model_name=model,
                    face_enhance=face_enhance,
                )
                
                progress.update(task, advance=40)
                console.print("[blue]Saving result...[/blue]")
                
                # Save result
                upscaled_image.save(output_path)
                
                progress.update(task, advance=10, completed=100)
            
            console.print(f"[green]Successfully upscaled image![/green]")
            console.print(f"[green]Input: {input_path} ({image.size})[/green]")
            console.print(f"[green]Output: {output_path} ({upscaled_image.size})[/green]")
            console.print(f"[green]Scale factor: {scale_factor}x[/green]")
            console.print(f"[green]Model: {model or config.upscaling.default_model}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error during upscaling: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_upscale())


@app.command()
def batch_upscale(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing images to upscale",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for upscaled images (default: input_dir/upscaled)",
    ),
    scale_factor: int = typer.Option(
        4,
        "--scale",
        "-s",
        min=2,
        max=4,
        help="Upscaling factor (2 or 4)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Upscaling model to use",
    ),
    pattern: str = typer.Option(
        "*.{png,jpg,jpeg,webp}",
        "--pattern",
        "-p",
        help="File pattern to match (glob style)",
    ),
    face_enhance: bool = typer.Option(
        False,
        "--face-enhance",
        "-f",
        help="Apply face enhancement",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Upscale multiple images in a directory."""
    async def _batch_upscale():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create upscaling service
            upscaling_service = create_upscaling_service(config)
            if upscaling_service is None:
                console.print("[red]Upscaling service not available[/red]")
                sys.exit(1)
            
            # Set up output directory
            if output_dir is None:
                output_dir = input_dir / "upscaled"
            output_dir.mkdir(exist_ok=True)
            
            # Find image files
            image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
            image_files = [
                f for f in input_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
            
            if not image_files:
                console.print(f"[yellow]No image files found in {input_dir}[/yellow]")
                return
            
            console.print(f"[blue]Found {len(image_files)} images to process[/blue]")
            
            # Process images
            with Progress() as progress:
                overall_task = progress.add_task("Processing images...", total=len(image_files))
                
                for i, image_file in enumerate(image_files, 1):
                    console.print(f"[blue]Processing {i}/{len(image_files)}: {image_file.name}[/blue]")
                    
                    try:
                        # Load image
                        image = Image.open(image_file)
                        
                        # Generate output path
                        output_path = output_dir / f"{image_file.stem}_upscaled_{scale_factor}x{image_file.suffix}"
                        
                        # Skip if already exists
                        if output_path.exists():
                            console.print(f"[yellow]Skipping {image_file.name} (already exists)[/yellow]")
                            progress.update(overall_task, advance=1)
                            continue
                        
                        # Upscale
                        upscaled_image = await upscaling_service.upscale_image(
                            image=image,
                            scale_factor=scale_factor,
                            model_name=model,
                            face_enhance=face_enhance,
                        )
                        
                        # Save
                        upscaled_image.save(output_path)
                        console.print(f"[green]✓ {image_file.name} -> {output_path.name}[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]✗ Error processing {image_file.name}: {e}[/red]")
                    
                    progress.update(overall_task, advance=1)
            
            console.print(f"[green]Batch upscaling completed![/green]")
            console.print(f"[green]Output directory: {output_dir}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error during batch upscaling: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_batch_upscale())


@app.command()
def generate_image(
    prompt: str = typer.Argument(..., help="Text prompt for image generation"),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output image path (optional)",
    ),
    enhance_prompt: bool = typer.Option(
        True,
        "--enhance/--no-enhance",
        help="Enhance prompt with AI",
    ),
    style: str = typer.Option(
        "photorealistic",
        "--style",
        "-s",
        help="Style for prompt enhancement",
    ),
    controlnet_type: Optional[str] = typer.Option(
        None,
        "--controlnet",
        help="ControlNet type (canny, depth, blur)",
    ),
    control_image: Optional[Path] = typer.Option(
        None,
        "--control-image",
        help="Control image for ControlNet",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducibility",
    ),
    steps: Optional[int] = typer.Option(
        None,
        "--steps",
        help="Number of inference steps",
    ),
    guidance: Optional[float] = typer.Option(
        None,
        "--guidance",
        help="Guidance scale",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Generate image using NVIDIA optimized Stable Diffusion 3.5."""
    async def _generate_image():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create image generation service
            image_service = create_image_generation_service(config)
            if image_service is None:
                console.print("[red]Image generation service not available. Please install dependencies:[/red]")
                console.print("pip install tensorrt nvidia-modelopt polygraphy")
                sys.exit(1)
            
            # Setup service if not already done
            console.print("🔧 Setting up NVIDIA SD3.5...")
            setup_success = await image_service.setup()
            if not setup_success:
                console.print("[red]Failed to setup image generation service[/red]")
                sys.exit(1)
            
            # Enhance prompt if requested
            working_prompt = prompt
            if enhance_prompt:
                console.print("🚀 Enhancing prompt...")
                prompt_enhancer = create_prompt_enhancer(config)
                if prompt_enhancer:
                    try:
                        enhanced = await prompt_enhancer.enhance_prompt(
                            prompt, style=style
                        )
                        working_prompt = enhanced["enhanced_prompt"]
                        console.print(f"✨ Enhanced: {working_prompt}")
                    except Exception as e:
                        console.print(f"[yellow]Prompt enhancement failed, using original: {e}[/yellow]")
            
            # Generate image
            console.print("🎨 Generating image with NVIDIA SD3.5...")
            
            start_time = time.time()
            
            if controlnet_type and control_image:
                result = await image_service.generate_controlnet_image(
                    prompt=working_prompt,
                    control_image_path=control_image,
                    controlnet_type=controlnet_type,
                    seed=seed,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    save_to_outputs=True
                )
            else:
                result = await image_service.generate_image(
                    prompt=working_prompt,
                    seed=seed,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    save_to_outputs=True
                )
            
            # Copy to custom output path if specified
            if output_path:
                import shutil
                shutil.copy2(result["image_path"], output_path)
                result["image_path"] = str(output_path)
            
            # Display results
            console.print(f"[green]✅ Image generation completed![/green]")
            console.print(f"[green]📸 Image: {result['image_path']}[/green]")
            console.print(f"[green]📐 Size: {result['dimensions']}[/green]")
            console.print(f"[blue]⏱️  Generation time: {result['generation_time']:.2f}s[/blue]")
            console.print(f"[blue]🧠 Backend: {result['backend']}[/blue]")
            console.print(f"[blue]🎯 Precision: {result['precision']}[/blue]")
            
        except Exception as e:
            console.print(f"[red]Error during image generation: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_generate_image())


@app.command()
def generate_video(
    prompt: str = typer.Argument(..., help="Text prompt for video generation"),
    output_name: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output video filename (optional)",
    ),
    precision: str = typer.Option(
        "fp8",
        "--precision",
        "-p",
        help="Precision setting (bf16, fp8)",
    ),
    enhance_prompt: bool = typer.Option(
        True,
        "--enhance/--no-enhance",
        help="Enhance prompt with AI",
    ),
    style: str = typer.Option(
        "photorealistic",
        "--style",
        "-s",
        help="Style for prompt enhancement",
    ),
    controlnet_type: Optional[str] = typer.Option(
        None,
        "--controlnet",
        help="ControlNet type (canny, depth, blur)",
    ),
    control_image: Optional[Path] = typer.Option(
        None,
        "--control-image",
        help="Control image for ControlNet",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducibility",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Generate video from text prompt using SD3.5 + SVD pipeline."""
    async def _generate_video():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create video pipeline (includes NVIDIA SD3.5 + SVD)
            video_pipeline = create_video_pipeline(config)
            if video_pipeline is None:
                console.print("[red]Video generation pipeline not available. Please install dependencies:[/red]")
                console.print("pip install tensorrt onnx onnxruntime-gpu ffmpeg-python imageio nvidia-modelopt")
                sys.exit(1)
            
            # Setup pipeline
            console.print("🔧 Setting up NVIDIA SD3.5 + SVD pipeline...")
            setup_success = await video_pipeline.setup()
            if not setup_success:
                console.print("[red]Failed to setup video pipeline[/red]")
                sys.exit(1)
            
            # Enhance prompt if requested
            working_prompt = prompt
            if enhance_prompt:
                console.print("🚀 Enhancing prompt...")
                prompt_enhancer = create_prompt_enhancer(config)
                if prompt_enhancer:
                    try:
                        enhanced = await prompt_enhancer.enhance_prompt(
                            prompt, style=style
                        )
                        working_prompt = enhanced["enhanced_prompt"]
                        console.print(f"✨ Enhanced: {working_prompt}")
                    except Exception as e:
                        console.print(f"[yellow]Prompt enhancement failed, using original: {e}[/yellow]")
            
            # Generate video
            console.print("🎬 Starting video generation pipeline...")
            
            start_time = time.time()
            result = await video_pipeline.text_to_video(
                prompt=working_prompt,
                precision=precision,
                seed=seed,
                controlnet_type=controlnet_type,
                control_image=control_image
            )
            
            # Display results
            console.print(f"[green]✅ Video generation completed![/green]")
            console.print(f"[green]📸 Image: {result['image']}[/green]")
            console.print(f"[green]🎥 Video: {result['video']}[/green]")
            console.print(f"[blue]⏱️  Image generation: {result['timings']['image_generation']:.2f}s[/blue]")
            console.print(f"[blue]⏱️  Video generation: {result['timings']['video_generation']:.2f}s[/blue]")
            console.print(f"[blue]⏱️  Total time: {result['timings']['total']:.2f}s[/blue]")
            
        except Exception as e:
            console.print(f"[red]Error during video generation: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_generate_video())


@app.command()
def batch_video(
    prompts_file: Path = typer.Argument(
        ...,
        help="JSON file containing prompts",
        exists=True,
        file_okay=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for videos",
    ),
    precision: str = typer.Option(
        "fp8",
        "--precision",
        "-p",
        help="Precision setting",
    ),
    max_concurrent: int = typer.Option(
        1,
        "--concurrent",
        help="Maximum concurrent generations",
    ),
    enhance_prompts: bool = typer.Option(
        True,
        "--enhance/--no-enhance",
        help="Enhance prompts with AI",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Batch generate videos from a list of prompts."""
    async def _batch_generate():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create video pipeline
            video_pipeline = create_video_pipeline(config)
            if video_pipeline is None:
                console.print("[red]Video generation pipeline not available[/red]")
                sys.exit(1)
            
            # Load prompts
            import json
            with open(prompts_file, 'r') as f:
                batch_data = json.load(f)
            
            if isinstance(batch_data, list):
                prompts = batch_data
            elif isinstance(batch_data, dict) and 'prompts' in batch_data:
                prompts = batch_data['prompts']
            else:
                raise ValueError("Invalid prompts file format")
            
            console.print(f"[blue]Loaded {len(prompts)} prompts for batch processing[/blue]")
            
            # Enhance prompts if requested
            if enhance_prompts:
                prompt_enhancer = create_prompt_enhancer(config)
                if prompt_enhancer:
                    console.print("🚀 Enhancing all prompts...")
                    enhanced_prompts = []
                    for prompt in prompts:
                        try:
                            enhanced = await prompt_enhancer.enhance_prompt(prompt)
                            enhanced_prompts.append(enhanced["enhanced_prompt"])
                        except Exception as e:
                            console.print(f"[yellow]Failed to enhance '{prompt[:30]}...': {e}[/yellow]")
                            enhanced_prompts.append(prompt)
                    prompts = enhanced_prompts
            
            # Batch generate
            console.print("🎬 Starting batch video generation...")
            results = await video_pipeline.batch_generate(
                prompts, 
                precision=precision, 
                max_concurrent=max_concurrent
            )
            
            # Display summary
            successful = sum(1 for r in results if "error" not in r)
            failed = len(results) - successful
            
            console.print(f"[green]✅ Batch generation completed![/green]")
            console.print(f"[green]📊 Successful: {successful}/{len(results)}[/green]")
            if failed > 0:
                console.print(f"[red]❌ Failed: {failed}/{len(results)}[/red]")
            
            # Show results
            for i, result in enumerate(results, 1):
                if "error" in result:
                    console.print(f"[red]{i}. Error: {result['error']}[/red]")
                else:
                    console.print(f"[green]{i}. Video: {result['video']}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error during batch generation: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_batch_generate())


@app.command()
def enhance_prompt(
    prompt: str = typer.Argument(..., help="Prompt to enhance"),
    style: str = typer.Option(
        "photorealistic",
        "--style",
        "-s",
        help="Enhancement style",
    ),
    complexity: str = typer.Option(
        "medium",
        "--complexity",
        "-c",
        help="Complexity level (simple, medium, detailed)",
    ),
    variations: int = typer.Option(
        0,
        "--variations",
        "-v",
        help="Number of variations to generate",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file",
    ),
) -> None:
    """Enhance a prompt using AI."""
    async def _enhance():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create prompt enhancer
            prompt_enhancer = create_prompt_enhancer(config)
            if prompt_enhancer is None:
                console.print("[red]Prompt enhancer not available. Please install ollama[/red]")
                sys.exit(1)
            
            # Enhance main prompt
            console.print(f"🚀 Enhancing prompt: {prompt}")
            enhanced = await prompt_enhancer.enhance_prompt(
                prompt, 
                style=style, 
                complexity_level=complexity
            )
            
            # Display results
            console.print("\n[bold blue]Original Prompt:[/bold blue]")
            console.print(f"  {enhanced['original_prompt']}")
            
            console.print("\n[bold green]Enhanced Prompt:[/bold green]")
            console.print(f"  {enhanced['enhanced_prompt']}")
            
            console.print("\n[bold yellow]Negative Prompt:[/bold yellow]")
            console.print(f"  {enhanced['negative_prompt']}")
            
            console.print(f"\n[blue]Style: {enhanced['style']} | Words: {enhanced['word_count']}[/blue]")
            
            # Generate variations if requested
            if variations > 0:
                console.print(f"\n🎨 Generating {variations} variations...")
                variation_results = await prompt_enhancer.generate_variations(
                    prompt, count=variations
                )
                
                for i, variation in enumerate(variation_results, 1):
                    console.print(f"\n[bold cyan]Variation {i}:[/bold cyan]")
                    console.print(f"  {variation['enhanced_prompt']}")
            
        except Exception as e:
            console.print(f"[red]Error during prompt enhancement: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_enhance())


@app.command()
def analyze_prompt(
    prompt: str = typer.Argument(..., help="Prompt to analyze"),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file",
    ),
) -> None:
    """Analyze a prompt and provide insights."""
    async def _analyze():
        try:
            # Load configuration
            config = load_config(config_file)
            
            # Create prompt enhancer
            prompt_enhancer = create_prompt_enhancer(config)
            if prompt_enhancer is None:
                console.print("[red]Prompt enhancer not available[/red]")
                sys.exit(1)
            
            # Analyze prompt
            console.print(f"🔍 Analyzing prompt: {prompt}")
            analysis = await prompt_enhancer.analyze_prompt(prompt)
            
            # Display analysis
            console.print(f"\n[bold blue]Prompt Analysis:[/bold blue]")
            console.print(f"  Prompt: {analysis['prompt']}")
            console.print(f"  Word Count: {analysis['word_count']}")
            console.print(f"  Character Count: {analysis['character_count']}")
            
            if "analysis" in analysis:
                console.print(f"\n[bold green]AI Analysis:[/bold green]")
                for key, value in analysis["analysis"].items():
                    console.print(f"  {key.replace('_', ' ').title()}: {value}")
            
        except Exception as e:
            console.print(f"[red]Error during prompt analysis: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(_analyze())


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"mini_muse version {__version__}")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()