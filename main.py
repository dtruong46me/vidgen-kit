import argparse
from src.pipeline.faceless_pipeline import FacelessPipeline

def main():
    parser = argparse.ArgumentParser(description="Faceless Video Generator MVP")
    parser.add_argument("script", help="Path to the input script JSON file")
    
    args = parser.parse_args()
    
    pipeline = FacelessPipeline()
    pipeline.run(args.script)

if __name__ == "__main__":
    main()
